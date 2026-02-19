import { Component, inject, OnInit, signal } from '@angular/core';
import { NavbarComponent } from '../ui/navbar.component';
import { ContentService, BlogPost } from '../../services/content.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-blog',
  standalone: true,
  imports: [NavbarComponent, CommonModule],
  template: `
    <app-navbar />
    <div class="min-h-screen bg-[#030304] text-white pt-32 pb-20">
      <div class="max-w-4xl mx-auto px-6">
        
        <div class="mb-16">
          <h1 class="text-4xl md:text-6xl font-display font-bold mb-4">Latest Updates</h1>
          <p class="text-zinc-400">Insights from the team building the future of creativity.</p>
        </div>

        @if (posts().length > 0) {
          <div class="space-y-12">
            @for (post of posts(); track post.id) {
              <article class="group cursor-pointer">
                <div class="overflow-hidden rounded-2xl mb-6 border border-white/5">
                  <img [src]="post.image_url" class="w-full h-64 object-cover opacity-80 group-hover:opacity-100 group-hover:scale-105 transition-all duration-700">
                </div>
                <div class="flex items-center gap-4 text-xs text-zinc-500 mb-3">
                  <span class="text-cyan-400 font-bold uppercase tracking-wider">{{ post.category }}</span>
                  <span>•</span>
                  <span>{{ post.date | date }}</span>
                </div>
                <h2 class="text-3xl font-bold mb-3 group-hover:text-cyan-400 transition-colors">{{ post.title }}</h2>
                <p class="text-zinc-400 leading-relaxed mb-4">{{ post.excerpt }}</p>
                <div class="flex items-center gap-2 text-sm font-medium">
                  <div class="w-6 h-6 rounded-full bg-zinc-800 flex items-center justify-center text-xs text-white">{{ post.author.charAt(0) }}</div>
                  <span>{{ post.author }}</span>
                </div>
              </article>
              <div class="h-px bg-white/5 my-12"></div>
            }
          </div>
        } @else {
          <div class="flex flex-col items-center justify-center py-20 opacity-50">
             <div class="text-4xl mb-4">📝</div>
             <p class="text-xl font-medium text-zinc-400">No blog posts yet.</p>
             <p class="text-sm text-zinc-600">Check back soon for updates.</p>
          </div>
        }

      </div>
    </div>
  `
})
export class BlogComponent implements OnInit {
  contentService = inject(ContentService);
  posts = signal<BlogPost[]>([]);

  ngOnInit() {
    this.contentService.getPosts().subscribe(p => this.posts.set(p));
  }
}