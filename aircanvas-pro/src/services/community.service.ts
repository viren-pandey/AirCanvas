import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

import { AuthService } from './auth.service';

export type CommunitySort = 'hot' | 'new' | 'top';

export interface CommunityPost {
  id: string;
  user_id: string;
  user_name: string;
  title: string;
  content: string;
  score: number;
  comment_count: number;
  user_vote: number;
  created_at: string;
}

export interface CommunityComment {
  id: string;
  post_id: string;
  user_id: string;
  user_name: string;
  parent_comment_id: string | null;
  content: string;
  created_at: string;
}

export interface ActivityEvent {
  id: string;
  user_id: string;
  activity_type: string;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface CommunityPostsPage {
  total: number;
  items: CommunityPost[];
}

export interface CommunityCommentsPage {
  total: number;
  items: CommunityComment[];
}

export interface ActivityEventsPage {
  total: number;
  items: ActivityEvent[];
}

@Injectable({
  providedIn: 'root'
})
export class CommunityService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);

  listPosts(sort: CommunitySort = 'hot', limit: number = 50, offset: number = 0): Observable<CommunityPostsPage> {
    return this.http.get<CommunityPostsPage>(
      this.apiUrl(`/community/posts?sort=${sort}&limit=${limit}&offset=${offset}`),
      { headers: this.jsonHeaders() },
    );
  }

  createPost(title: string, content: string): Observable<CommunityPost> {
    return this.http.post<CommunityPost>(
      this.apiUrl('/community/posts'),
      { title, content },
      { headers: this.jsonHeaders() },
    );
  }

  votePost(postId: string, value: -1 | 0 | 1): Observable<CommunityPost> {
    return this.http.post<CommunityPost>(
      this.apiUrl(`/community/posts/${postId}/vote`),
      { value },
      { headers: this.jsonHeaders() },
    );
  }

  listComments(postId: string, limit: number = 120, offset: number = 0): Observable<CommunityCommentsPage> {
    return this.http.get<CommunityCommentsPage>(
      this.apiUrl(`/community/posts/${postId}/comments?limit=${limit}&offset=${offset}`),
      { headers: this.jsonHeaders() },
    );
  }

  createComment(postId: string, content: string): Observable<CommunityComment> {
    return this.http.post<CommunityComment>(
      this.apiUrl(`/community/posts/${postId}/comments`),
      { content },
      { headers: this.jsonHeaders() },
    );
  }

  listMyActivity(limit: number = 40, offset: number = 0): Observable<ActivityEventsPage> {
    return this.http.get<ActivityEventsPage>(
      this.apiUrl(`/community/activity?limit=${limit}&offset=${offset}`),
      { headers: this.jsonHeaders() },
    );
  }

  private apiUrl(path: string): string {
    return `${this.auth.apiBaseUrl()}${this.auth.apiPrefix()}${path}`;
  }

  private jsonHeaders(): HttpHeaders {
    return new HttpHeaders(this.auth.authHeaders(true));
  }
}
