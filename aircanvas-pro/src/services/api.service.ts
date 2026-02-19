import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, catchError, from, map, switchMap, throwError } from 'rxjs';
import { AuthService } from './auth.service';

export interface CanvasSession {
  id: string;
  userId: string;
  startedAt: string;
  endedAt?: string;
  avgFps: number;
}

interface SessionOut {
  id: string;
  user_id: string;
  session_start: string;
  session_end?: string;
  avg_fps?: number;
}

interface UploadUrlResponse {
  frame_id: string;
  frame_upload_url: string;
  thumbnail_upload_url: string;
}

interface FrameCompleteResponse {
  id: string;
  frame_url: string;
  thumbnail_url?: string;
  created_at: string;
}

export interface SavedFrame {
  id: string;
  user_id: string;
  session_id?: string;
  frame_url: string;
  thumbnail_url?: string;
  created_at: string;
  brush_mode?: string;
  shape_mode?: string;
}

interface SavedFramesPage {
  total: number;
  items: SavedFrame[];
}

export interface DesktopLaunchResponse {
  started: boolean;
  already_running: boolean;
  pid: number | null;
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);

  startSession(_userId: string): Observable<CanvasSession> {
    return this.http
      .post<SessionOut>(
        this.apiUrl('/sessions'),
        { session_start: new Date().toISOString() },
        { headers: this.jsonHeaders() },
      )
      .pipe(map((session) => this.mapSession(session)));
  }

  endSession(sessionId: string, avgFps: number): Observable<CanvasSession> {
    return this.http
      .patch<SessionOut>(
        this.apiUrl(`/sessions/${sessionId}/end`),
        {
          session_end: new Date().toISOString(),
          avg_fps: avgFps,
        },
        { headers: this.jsonHeaders() },
      )
      .pipe(map((session) => this.mapSession(session)));
  }

  uploadFrame(
    sessionId: string,
    blob: Blob,
    brushMode: string = 'web_canvas',
    shapeMode: string = 'free_draw',
  ): Observable<FrameCompleteResponse> {
    return this.http
      .post<UploadUrlResponse>(
        this.apiUrl('/frames/upload-url'),
        {
          session_id: sessionId,
          brush_mode: brushMode,
          shape_mode: shapeMode,
          frame_extension: 'png',
          thumbnail_extension: 'jpg',
        },
        { headers: this.jsonHeaders() },
      )
      .pipe(
        switchMap((ticket) => from(this.uploadToSignedUrls(ticket, blob)).pipe(map(() => ticket))),
        switchMap((ticket) =>
          this.http.post<FrameCompleteResponse>(
            this.apiUrl(`/frames/${ticket.frame_id}/complete`),
            {},
            { headers: this.jsonHeaders() },
          ),
        ),
        catchError((error) => throwError(() => error)),
      );
  }

  listFrames(limit: number = 12, offset: number = 0): Observable<SavedFramesPage> {
    return this.http.get<SavedFramesPage>(
      this.apiUrl(`/frames?limit=${limit}&offset=${offset}`),
      { headers: this.jsonHeaders() },
    );
  }

  launchDesktopApp(): Observable<DesktopLaunchResponse> {
    return this.http.post<DesktopLaunchResponse>(
      this.apiUrl('/desktop/launch'),
      {},
      { headers: this.jsonHeaders() },
    );
  }

  private mapSession(item: SessionOut): CanvasSession {
    return {
      id: item.id,
      userId: item.user_id,
      startedAt: item.session_start,
      endedAt: item.session_end,
      avgFps: Number(item.avg_fps ?? 0),
    };
  }

  private apiUrl(path: string): string {
    return `${this.auth.apiBaseUrl()}${this.auth.apiPrefix()}${path}`;
  }

  private jsonHeaders(): HttpHeaders {
    return new HttpHeaders(this.auth.authHeaders(true));
  }

  private async uploadToSignedUrls(ticket: UploadUrlResponse, blob: Blob): Promise<void> {
    const thumbnail = await this.createThumbnailBlob(blob);
    await this.putToSignedUrl(ticket.frame_upload_url, blob, 'image/png');
    await this.putToSignedUrl(ticket.thumbnail_upload_url, thumbnail, 'image/jpeg');
  }

  private async putToSignedUrl(url: string, blob: Blob, contentType: string): Promise<void> {
    const response = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': contentType },
      body: blob,
    });
    if (!response.ok) {
      throw new Error(`Signed upload failed (${response.status})`);
    }
  }

  private async createThumbnailBlob(sourceBlob: Blob): Promise<Blob> {
    try {
      const bitmap = await createImageBitmap(sourceBlob);
      const maxWidth = 420;
      const scale = Math.min(1, maxWidth / bitmap.width);
      const width = Math.max(1, Math.round(bitmap.width * scale));
      const height = Math.max(1, Math.round(bitmap.height * scale));

      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        bitmap.close();
        return sourceBlob;
      }

      ctx.drawImage(bitmap, 0, 0, width, height);
      bitmap.close();

      return await new Promise<Blob>((resolve) => {
        canvas.toBlob((thumb) => resolve(thumb ?? sourceBlob), 'image/jpeg', 0.78);
      });
    } catch {
      return sourceBlob;
    }
  }
}
