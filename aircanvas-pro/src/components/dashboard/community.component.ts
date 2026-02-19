import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { SidebarComponent } from '../ui/sidebar.component';
import {
  ActivityEvent,
  CommunityComment,
  CommunityPost,
  CommunityService,
  CommunitySort,
} from '../../services/community.service';

@Component({
  selector: 'app-community',
  standalone: true,
  imports: [CommonModule, FormsModule, SidebarComponent],
  template: `
    <div class="flex min-h-screen w-full bg-[#030304] text-white font-sans">
      <app-sidebar />
      <main class="flex-1 flex flex-col relative bg-[#030304] pl-20 lg:pl-72 transition-all duration-300">
        <div class="p-8 h-full flex flex-col gap-6">
          <div>
            <h1 class="text-4xl font-display font-bold mb-2">r/AirCanvas</h1>
            <p class="text-zinc-400">Reddit-style community feed with votes, comments, and live maker activity.</p>
          </div>

          <div class="grid grid-cols-1 xl:grid-cols-3 gap-6 flex-1 min-h-0">
            <section class="xl:col-span-2 flex flex-col min-h-0 gap-4">
              <div class="rounded-xl border border-zinc-800 bg-[#0A0A0C] p-4">
                <div class="text-xs uppercase tracking-wider text-zinc-500 mb-2">Create Post</div>
                <input
                  [(ngModel)]="titleDraft"
                  maxlength="220"
                  placeholder="Post title"
                  class="w-full bg-black/40 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-orange-500"
                />
                <textarea
                  [(ngModel)]="bodyDraft"
                  maxlength="2400"
                  rows="4"
                  placeholder="Text (optional but recommended)"
                  class="w-full mt-3 bg-black/40 border border-zinc-700 rounded-lg p-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-orange-500"
                ></textarea>
                <div class="mt-3 flex items-center justify-between gap-3">
                  <span class="text-xs text-zinc-500">{{ bodyDraft.length }}/2400</span>
                  <button
                    (click)="publishPost()"
                    [disabled]="isPublishing() || !canPublish()"
                    class="px-4 py-2 bg-orange-600 text-white rounded-lg font-bold text-sm hover:bg-orange-500 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {{ isPublishing() ? 'Posting...' : 'Post' }}
                  </button>
                </div>
                @if (publishError()) {
                  <div class="text-sm text-red-400 mt-2">{{ publishError() }}</div>
                }
              </div>

              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <button
                    (click)="setSort('hot')"
                    class="px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors"
                    [class.bg-orange-600]="sort() === 'hot'"
                    [class.border-orange-500]="sort() === 'hot'"
                    [class.border-zinc-700]="sort() !== 'hot'"
                    [class.text-zinc-200]="sort() !== 'hot'"
                  >
                    Hot
                  </button>
                  <button
                    (click)="setSort('new')"
                    class="px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors"
                    [class.bg-orange-600]="sort() === 'new'"
                    [class.border-orange-500]="sort() === 'new'"
                    [class.border-zinc-700]="sort() !== 'new'"
                    [class.text-zinc-200]="sort() !== 'new'"
                  >
                    New
                  </button>
                  <button
                    (click)="setSort('top')"
                    class="px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors"
                    [class.bg-orange-600]="sort() === 'top'"
                    [class.border-orange-500]="sort() === 'top'"
                    [class.border-zinc-700]="sort() !== 'top'"
                    [class.text-zinc-200]="sort() !== 'top'"
                  >
                    Top
                  </button>
                </div>
                <button (click)="refreshAll()" class="text-xs text-zinc-400 hover:text-white transition-colors">Refresh</button>
              </div>

              <div class="flex-1 min-h-0 overflow-y-auto pr-1 space-y-3">
                @if (isLoadingPosts()) {
                  <div class="p-6 rounded-xl border border-zinc-800 bg-[#0A0A0C] text-zinc-400 text-sm">Loading posts...</div>
                } @else if (!posts().length) {
                  <div class="p-6 rounded-xl border border-dashed border-zinc-700 bg-[#0A0A0C] text-zinc-400 text-sm">
                    No posts yet. Start the first thread.
                  </div>
                } @else {
                  @for (post of posts(); track post.id) {
                    <article class="rounded-xl border border-zinc-800 bg-[#0A0A0C] overflow-hidden">
                      <div class="grid grid-cols-[48px_1fr]">
                        <div class="bg-black/30 border-r border-zinc-800 flex flex-col items-center py-3 gap-2">
                          <button (click)="vote(post, 1)" class="w-6 h-6 rounded hover:bg-white/10" [class.text-orange-400]="post.user_vote === 1">
                            ▲
                          </button>
                          <div class="text-xs font-bold text-zinc-200">{{ post.score }}</div>
                          <button (click)="vote(post, -1)" class="w-6 h-6 rounded hover:bg-white/10" [class.text-blue-400]="post.user_vote === -1">
                            ▼
                          </button>
                        </div>

                        <div class="p-4">
                          <div class="text-xs text-zinc-500 mb-1">
                            posted by <span class="text-zinc-300">u/{{ post.user_name }}</span> {{ relativeTime(post.created_at) }}
                          </div>
                          <h3 class="text-lg font-bold text-white leading-tight">{{ post.title }}</h3>
                          <p class="text-sm text-zinc-300 whitespace-pre-wrap mt-2">{{ post.content }}</p>

                          <div class="mt-4 flex items-center gap-4 text-xs text-zinc-500">
                            <button (click)="toggleComments(post.id)" class="hover:text-zinc-200 transition-colors">
                              {{ post.comment_count }} comments
                            </button>
                            <span>{{ post.score }} points</span>
                          </div>

                          @if (expandedPostId() === post.id) {
                            <div class="mt-4 border-t border-zinc-800 pt-4">
                              <div class="mb-3">
                                <textarea
                                  [ngModel]="commentDraft(post.id)"
                                  (ngModelChange)="setCommentDraft(post.id, $event)"
                                  rows="3"
                                  maxlength="1200"
                                  placeholder="Add a comment"
                                  class="w-full bg-black/40 border border-zinc-700 rounded-lg p-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-orange-500"
                                ></textarea>
                                <div class="mt-2 flex items-center justify-between">
                                  <span class="text-xs text-zinc-500">{{ commentDraft(post.id).length }}/1200</span>
                                  <button
                                    (click)="publishComment(post)"
                                    [disabled]="isPostingComment(post.id) || !commentDraft(post.id).trim()"
                                    class="px-3 py-1.5 bg-zinc-100 text-black rounded-md text-xs font-bold hover:bg-white disabled:opacity-60 disabled:cursor-not-allowed"
                                  >
                                    {{ isPostingComment(post.id) ? 'Posting...' : 'Comment' }}
                                  </button>
                                </div>
                                @if (commentError(post.id)) {
                                  <div class="text-xs text-red-400 mt-2">{{ commentError(post.id) }}</div>
                                }
                              </div>

                              @if (isCommentsLoading(post.id)) {
                                <div class="text-xs text-zinc-500">Loading comments...</div>
                              } @else if (!commentsFor(post.id).length) {
                                <div class="text-xs text-zinc-500">No comments yet.</div>
                              } @else {
                                <div class="space-y-2">
                                  @for (comment of commentsFor(post.id); track comment.id) {
                                    <div class="rounded-lg border border-zinc-800 bg-black/30 p-3">
                                      <div class="text-xs text-zinc-500 mb-1">
                                        <span class="text-zinc-300">u/{{ comment.user_name }}</span> {{ relativeTime(comment.created_at) }}
                                      </div>
                                      <p class="text-sm text-zinc-300 whitespace-pre-wrap">{{ comment.content }}</p>
                                    </div>
                                  }
                                </div>
                              }
                            </div>
                          }
                        </div>
                      </div>
                    </article>
                  }
                }
              </div>
            </section>

            <aside class="rounded-xl border border-zinc-800 bg-[#0A0A0C] p-4 flex flex-col min-h-0">
              <div class="mb-4">
                <h2 class="text-lg font-bold">Community Stats</h2>
                <div class="mt-2 text-sm text-zinc-400">Posts: <span class="text-white">{{ posts().length }}</span></div>
                <div class="text-sm text-zinc-400">Total score: <span class="text-white">{{ totalScore() }}</span></div>
              </div>

              <div class="border-t border-zinc-800 pt-4 mb-4">
                <h3 class="text-sm font-bold mb-2">Top Threads</h3>
                @if (!topThreads().length) {
                  <div class="text-xs text-zinc-500">No ranked posts yet.</div>
                } @else {
                  <div class="space-y-2">
                    @for (item of topThreads(); track item.id) {
                      <div class="text-xs text-zinc-300 truncate">
                        <span class="text-orange-300 mr-1">{{ item.score }}</span>{{ item.title }}
                      </div>
                    }
                  </div>
                }
              </div>

              <div class="border-t border-zinc-800 pt-4 flex-1 min-h-0 flex flex-col">
                <div class="flex items-center justify-between mb-2">
                  <h3 class="text-sm font-bold">My Activity</h3>
                  <span class="text-xs text-zinc-500">{{ activities().length }}</span>
                </div>
                <div class="flex-1 min-h-0 overflow-y-auto pr-1 space-y-2">
                  @if (isLoadingActivity()) {
                    <div class="text-xs text-zinc-500">Loading activity...</div>
                  } @else if (!activities().length) {
                    <div class="text-xs text-zinc-500">No recent activity.</div>
                  } @else {
                    @for (event of activities(); track event.id) {
                      <div class="rounded-lg border border-zinc-800 bg-black/30 p-2">
                        <div class="text-xs text-zinc-200">{{ humanizeActivity(event.activity_type) }}</div>
                        <div class="text-[11px] text-zinc-500 mt-1">{{ relativeTime(event.created_at) }}</div>
                      </div>
                    }
                  }
                </div>
              </div>
            </aside>
          </div>
        </div>
      </main>
    </div>
  `
})
export class CommunityComponent implements OnInit {
  private community = inject(CommunityService);

  sort = signal<CommunitySort>('hot');
  titleDraft = '';
  bodyDraft = '';

  posts = signal<CommunityPost[]>([]);
  activities = signal<ActivityEvent[]>([]);

  commentsByPost = signal<Record<string, CommunityComment[]>>({});
  commentsLoadingByPost = signal<Record<string, boolean>>({});
  postingCommentByPost = signal<Record<string, boolean>>({});
  commentDraftByPost = signal<Record<string, string>>({});
  commentErrorByPost = signal<Record<string, string>>({});
  expandedPostId = signal<string | null>(null);

  isLoadingPosts = signal<boolean>(false);
  isLoadingActivity = signal<boolean>(false);
  isPublishing = signal<boolean>(false);
  publishError = signal<string>('');

  ngOnInit(): void {
    this.refreshAll();
  }

  canPublish(): boolean {
    return Boolean(this.titleDraft.trim() || this.bodyDraft.trim());
  }

  setSort(sort: CommunitySort): void {
    if (this.sort() === sort) {
      return;
    }
    this.sort.set(sort);
    this.loadPosts();
  }

  refreshAll(): void {
    this.loadPosts();
    this.loadActivity();
  }

  publishPost(): void {
    if (!this.canPublish()) {
      return;
    }
    this.isPublishing.set(true);
    this.publishError.set('');

    const title = this.titleDraft.trim();
    const content = this.bodyDraft.trim() || title;
    this.community.createPost(title, content).subscribe({
      next: () => {
        this.titleDraft = '';
        this.bodyDraft = '';
        this.isPublishing.set(false);
        this.loadPosts();
      },
      error: (err: unknown) => {
        this.isPublishing.set(false);
        this.publishError.set(this.errorText(err, 'Unable to publish post.'));
      },
    });
  }

  vote(post: CommunityPost, direction: -1 | 1): void {
    const desired = post.user_vote === direction ? 0 : direction;
    this.community.votePost(post.id, desired as -1 | 0 | 1).subscribe({
      next: (updated) => {
        this.posts.update((items) =>
          items.map((item) => (item.id === post.id ? { ...item, ...updated } : item)),
        );
      },
      error: () => {
        // Keep current UI state on vote errors.
      },
    });
  }

  toggleComments(postId: string): void {
    if (this.expandedPostId() === postId) {
      this.expandedPostId.set(null);
      return;
    }
    this.expandedPostId.set(postId);
    if (!this.commentsByPost()[postId]) {
      this.loadComments(postId);
    }
  }

  loadComments(postId: string): void {
    this.patchMap(this.commentsLoadingByPost, postId, true);
    this.patchMap(this.commentErrorByPost, postId, '');
    this.community.listComments(postId, 200, 0).subscribe({
      next: (page) => {
        this.commentsByPost.update((all) => ({ ...all, [postId]: page.items || [] }));
        this.patchMap(this.commentsLoadingByPost, postId, false);
      },
      error: (err: unknown) => {
        this.patchMap(this.commentsLoadingByPost, postId, false);
        this.patchMap(this.commentErrorByPost, postId, this.errorText(err, 'Failed to load comments.'));
      },
    });
  }

  publishComment(post: CommunityPost): void {
    const content = this.commentDraft(post.id).trim();
    if (!content) {
      return;
    }
    this.patchMap(this.postingCommentByPost, post.id, true);
    this.patchMap(this.commentErrorByPost, post.id, '');
    this.community.createComment(post.id, content).subscribe({
      next: (comment) => {
        this.commentsByPost.update((all) => ({
          ...all,
          [post.id]: [...(all[post.id] || []), comment],
        }));
        this.patchMap(this.commentDraftByPost, post.id, '');
        this.patchMap(this.postingCommentByPost, post.id, false);
        this.posts.update((items) =>
          items.map((item) =>
            item.id === post.id ? { ...item, comment_count: Number(item.comment_count || 0) + 1 } : item,
          ),
        );
      },
      error: (err: unknown) => {
        this.patchMap(this.postingCommentByPost, post.id, false);
        this.patchMap(this.commentErrorByPost, post.id, this.errorText(err, 'Failed to post comment.'));
      },
    });
  }

  commentsFor(postId: string): CommunityComment[] {
    return this.commentsByPost()[postId] || [];
  }

  isCommentsLoading(postId: string): boolean {
    return Boolean(this.commentsLoadingByPost()[postId]);
  }

  isPostingComment(postId: string): boolean {
    return Boolean(this.postingCommentByPost()[postId]);
  }

  setCommentDraft(postId: string, value: string): void {
    this.patchMap(this.commentDraftByPost, postId, value);
  }

  commentDraft(postId: string): string {
    return this.commentDraftByPost()[postId] || '';
  }

  commentError(postId: string): string {
    return this.commentErrorByPost()[postId] || '';
  }

  totalScore(): number {
    return this.posts().reduce((sum, item) => sum + Number(item.score || 0), 0);
  }

  topThreads(): CommunityPost[] {
    return [...this.posts()]
      .sort((a, b) => Number(b.score || 0) - Number(a.score || 0))
      .slice(0, 5);
  }

  relativeTime(value: string): string {
    const then = new Date(value).getTime();
    if (!Number.isFinite(then)) {
      return '';
    }
    const diffMs = Date.now() - then;
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) {
      return 'just now';
    }
    if (diffMin < 60) {
      return `${diffMin}m ago`;
    }
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) {
      return `${diffHr}h ago`;
    }
    const diffDay = Math.floor(diffHr / 24);
    return `${diffDay}d ago`;
  }

  humanizeActivity(activityType: string): string {
    const map: Record<string, string> = {
      account_registered: 'Account registered',
      account_login: 'Logged in',
      session_started: 'Session started',
      session_ended: 'Session ended',
      frame_upload_requested: 'Frame upload requested',
      frame_upload_completed: 'Frame upload completed',
      community_post_created: 'Created a post',
      community_post_voted: 'Voted on a post',
      community_comment_created: 'Added a comment',
      desktop_app_launched: 'Launched AirCanvas4 desktop',
    };
    return map[activityType] || activityType.replaceAll('_', ' ');
  }

  private loadPosts(): void {
    this.isLoadingPosts.set(true);
    this.community.listPosts(this.sort(), 80, 0).subscribe({
      next: (page) => {
        this.posts.set(page.items || []);
        this.isLoadingPosts.set(false);
      },
      error: () => {
        this.posts.set([]);
        this.isLoadingPosts.set(false);
      },
    });
  }

  private loadActivity(): void {
    this.isLoadingActivity.set(true);
    this.community.listMyActivity(80, 0).subscribe({
      next: (page) => {
        this.activities.set(page.items || []);
        this.isLoadingActivity.set(false);
      },
      error: () => {
        this.activities.set([]);
        this.isLoadingActivity.set(false);
      },
    });
  }

  private patchMap<T extends string | boolean>(
    state: { update: (fn: (current: Record<string, T>) => Record<string, T>) => void },
    key: string,
    value: T,
  ): void {
    state.update((current) => ({ ...current, [key]: value }));
  }

  private errorText(err: unknown, fallback: string): string {
    if (err instanceof Error && err.message) {
      return err.message;
    }
    return fallback;
  }
}
