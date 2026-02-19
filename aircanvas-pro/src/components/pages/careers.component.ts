import { Component, inject, OnInit, signal } from '@angular/core';
import { NavbarComponent } from '../ui/navbar.component';
import { ContentService, JobPost } from '../../services/content.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-careers',
  standalone: true,
  imports: [NavbarComponent, CommonModule],
  template: `
    <app-navbar />
    <div class="min-h-screen bg-[#030304] text-white pt-32 pb-20">
      <div class="max-w-4xl mx-auto px-6">
        
        <div class="text-center mb-24">
          <h1 class="text-5xl md:text-7xl font-display font-bold mb-8">Join the Revolution</h1>
          <p class="text-xl text-zinc-400 max-w-2xl mx-auto mb-8">We're building the operating system for the spatial web. Come define the future of human-computer interaction.</p>
          <div class="flex justify-center gap-12 text-center">
            <div>
               <div class="text-3xl font-bold mb-1">remote</div>
               <div class="text-xs text-zinc-500 uppercase tracking-widest">Culture</div>
            </div>
             <div>
               <div class="text-3xl font-bold mb-1">$10M+</div>
               <div class="text-xs text-zinc-500 uppercase tracking-widest">Funding</div>
            </div>
             <div>
               <div class="text-3xl font-bold mb-1">15+</div>
               <div class="text-xs text-zinc-500 uppercase tracking-widest">Countries</div>
            </div>
          </div>
        </div>

        <h2 class="text-sm font-bold text-zinc-500 uppercase tracking-widest mb-8 border-b border-white/10 pb-4">Open Positions</h2>

        @if (jobs().length > 0) {
          <div class="space-y-4">
            @for (job of jobs(); track job.id) {
              <div class="p-6 rounded-xl border border-white/5 bg-[#0A0A0C] hover:border-white/20 transition-all flex justify-between items-center group cursor-pointer">
                <div>
                  <h3 class="text-xl font-bold mb-1 group-hover:text-cyan-400 transition-colors">{{ job.title }}</h3>
                  <div class="flex gap-4 text-sm text-zinc-500">
                    <span>{{ job.department }}</span>
                    <span>•</span>
                    <span>{{ job.location }}</span>
                    <span>•</span>
                    <span>{{ job.type }}</span>
                  </div>
                </div>
                <div class="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center group-hover:bg-white group-hover:text-black transition-all">
                  <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                </div>
              </div>
            }
          </div>
        } @else {
          <div class="flex flex-col items-center justify-center py-20 opacity-50">
             <div class="text-4xl mb-4">🚀</div>
             <p class="text-xl font-medium text-zinc-400">No open positions right now.</p>
             <p class="text-sm text-zinc-600">We are always looking for talent. Email us your resume.</p>
          </div>
        }

      </div>
    </div>
  `
})
export class CareersComponent implements OnInit {
  contentService = inject(ContentService);
  jobs = signal<JobPost[]>([]);

  ngOnInit() {
    this.contentService.getJobs().subscribe(j => this.jobs.set(j));
  }
}