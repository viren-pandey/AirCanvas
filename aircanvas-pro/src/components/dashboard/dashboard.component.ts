import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { ApiService, SavedFrame } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { SidebarComponent } from '../ui/sidebar.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, SidebarComponent],
  template: `
    <div class="flex min-h-screen w-full bg-[#030304] text-white font-sans">
      <app-sidebar />
      <main class="flex-1 flex flex-col relative bg-[#030304] pl-20 lg:pl-72 transition-all duration-300">
        <header class="h-16 border-b border-white/5 flex items-center justify-between px-8 bg-[#030304]/80 backdrop-blur sticky top-0 z-10">
          <div class="flex items-center gap-4">
            <span class="text-sm font-bold text-white">Dashboard</span>
          </div>

          <div class="flex items-center gap-6">
            <div (click)="goToProfile()" class="flex items-center gap-3 pl-6 border-l border-white/5 cursor-pointer hover:opacity-80 transition-opacity">
              <div class="text-right hidden md:block">
                <div class="text-xs font-bold text-white">{{ auth.user()?.name }}</div>
                <div class="text-[10px] text-zinc-500 uppercase tracking-wider">Creator Plan</div>
              </div>
              <div class="w-8 h-8 rounded bg-zinc-800 border border-white/10 flex items-center justify-center text-xs font-bold">
                {{ auth.user()?.name?.charAt(0) }}
              </div>
            </div>
          </div>
        </header>

        <div class="flex-1 overflow-auto p-8 relative">
          <h1 class="text-3xl font-bold mb-2">Welcome, {{ auth.user()?.name?.split(' ')?.[0] }}</h1>
          <p class="text-zinc-400 mb-8">Launch AirCanvas4 desktop (main.py) or draw in web canvas. Every save is stored locally and synced to DB.</p>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <button
              (click)="launchAirCanvasDesktop()"
              [disabled]="isLaunchingDesktop()"
              class="p-6 rounded-xl border border-zinc-700 bg-[#0A0A0C] hover:border-cyan-500 hover:bg-cyan-500/10 text-left transition-all disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <div class="text-xs uppercase tracking-wider text-zinc-500 mb-2">Desktop Runtime</div>
              <div class="text-lg font-bold mb-1">Launch AirCanvas4 (main.py)</div>
              <div class="text-sm text-zinc-400">Opens the native app and injects your token so save events sync to PostgreSQL.</div>
            </button>

            <button
              (click)="openCanvas()"
              class="p-6 rounded-xl border border-zinc-700 bg-[#0A0A0C] hover:border-blue-500 hover:bg-blue-500/10 text-left transition-all"
            >
              <div class="text-xs uppercase tracking-wider text-zinc-500 mb-2">Browser Canvas</div>
              <div class="text-lg font-bold mb-1">Open Web Canvas</div>
              <div class="text-sm text-zinc-400">Stay in browser and continue with collaborative whiteboard mode.</div>
            </button>
          </div>

          @if (desktopMessage()) {
            <div class="mt-4 rounded-lg border px-4 py-3 text-sm" [class.border-red-500/40]="desktopError()" [class.text-red-300]="desktopError()" [class.border-emerald-500/30]="!desktopError()" [class.text-emerald-300]="!desktopError()">
              {{ desktopMessage() }}
            </div>
          }

          <section class="mt-10">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-xl font-bold">Recent Saves</h2>
              <button (click)="loadRecentSaves()" class="text-xs text-zinc-400 hover:text-white">Refresh</button>
            </div>

            @if (isLoadingSaves()) {
              <div class="rounded-xl border border-zinc-800 bg-[#0A0A0C] p-6 text-zinc-400 text-sm">Loading saved frames...</div>
            } @else if (!recentSaves().length) {
              <div class="rounded-xl border border-dashed border-zinc-700 bg-[#0A0A0C] p-6 text-zinc-400 text-sm">
                No saved frames yet. Save from web canvas or AirCanvas4 desktop and refresh this panel.
              </div>
            } @else {
              <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                @for (frame of recentSaves(); track frame.id) {
                  <article class="rounded-xl border border-zinc-800 bg-[#0A0A0C] overflow-hidden">
                    @if (frame.thumbnail_url) {
                      <img [src]="frame.thumbnail_url" alt="Saved frame thumbnail" class="w-full h-44 object-cover bg-black/30" />
                    } @else {
                      <div class="w-full h-44 bg-black/40 flex items-center justify-center text-zinc-600 text-sm">No preview</div>
                    }
                    <div class="p-4">
                      <div class="text-sm text-zinc-200 font-semibold truncate">{{ frame.shape_mode || 'free_draw' }}</div>
                      <div class="text-xs text-zinc-500 mt-1">{{ frame.brush_mode || 'brush' }} | {{ formatDate(frame.created_at) }}</div>
                      <a [href]="frame.frame_url" target="_blank" rel="noreferrer" class="inline-flex mt-3 text-xs text-cyan-300 hover:text-cyan-200">
                        Open Saved Frame
                      </a>
                    </div>
                  </article>
                }
              </div>
            }
          </section>
        </div>
      </main>
    </div>
  `
})
export class DashboardComponent implements OnInit {
  auth = inject(AuthService);
  router = inject(Router);
  private api = inject(ApiService);

  recentSaves = signal<SavedFrame[]>([]);
  isLoadingSaves = signal<boolean>(false);
  isLaunchingDesktop = signal<boolean>(false);
  desktopMessage = signal<string>('');
  desktopError = signal<boolean>(false);

  ngOnInit(): void {
    this.loadRecentSaves();
  }

  launchAirCanvasDesktop(): void {
    this.isLaunchingDesktop.set(true);
    this.desktopMessage.set('');
    this.desktopError.set(false);

    this.api.launchDesktopApp().subscribe({
      next: (response) => {
        this.desktopMessage.set(response.message + (response.pid ? ` (PID: ${response.pid})` : ''));
        this.desktopError.set(false);
        this.isLaunchingDesktop.set(false);
      },
      error: (err: unknown) => {
        const message = err instanceof Error ? err.message : 'Failed to launch AirCanvas4 desktop.';
        this.desktopMessage.set(message);
        this.desktopError.set(true);
        this.isLaunchingDesktop.set(false);
      },
    });
  }

  loadRecentSaves(): void {
    this.isLoadingSaves.set(true);
    this.api.listFrames(18, 0).subscribe({
      next: (page) => {
        this.recentSaves.set(page.items || []);
        this.isLoadingSaves.set(false);
      },
      error: () => {
        this.recentSaves.set([]);
        this.isLoadingSaves.set(false);
      },
    });
  }

  openCanvas(): void {
    this.router.navigate(['/canvas']);
  }

  goToProfile(): void {
    this.router.navigate(['/profile']);
  }

  formatDate(value: string): string {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return '-';
    }
    return parsed.toLocaleString();
  }
}
