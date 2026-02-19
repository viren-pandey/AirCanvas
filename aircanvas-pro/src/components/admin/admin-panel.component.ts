import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ContentService, BlogPost, JobPost } from '../../services/content.service';
import { ReactiveFormsModule, FormBuilder, Validators, FormGroup } from '@angular/forms';

type AdminTab = 'DASHBOARD' | 'BLOG' | 'CAREERS';

@Component({
  selector: 'app-admin-panel',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule],
  template: `
    <div class="flex min-h-screen bg-[#0B0F1A] text-white font-sans">
      
      <!-- Sidebar -->
      <aside class="w-64 border-r border-white/5 bg-[#05050A] flex flex-col">
        <div class="h-16 flex items-center px-6 border-b border-white/5">
          <span class="font-display font-bold text-lg text-cyan-400">AC Admin</span>
        </div>
        <nav class="p-4 space-y-1">
          <button (click)="tab.set('DASHBOARD')" class="w-full text-left px-4 py-2 rounded text-sm font-medium transition-colors" [ngClass]="tab() === 'DASHBOARD' ? 'bg-cyan-500/10 text-cyan-400' : 'text-zinc-400 hover:text-white'">Overview</button>
          <button (click)="tab.set('BLOG')" class="w-full text-left px-4 py-2 rounded text-sm font-medium transition-colors" [ngClass]="tab() === 'BLOG' ? 'bg-cyan-500/10 text-cyan-400' : 'text-zinc-400 hover:text-white'">Blog Posts</button>
          <button (click)="tab.set('CAREERS')" class="w-full text-left px-4 py-2 rounded text-sm font-medium transition-colors" [ngClass]="tab() === 'CAREERS' ? 'bg-cyan-500/10 text-cyan-400' : 'text-zinc-400 hover:text-white'">Careers</button>
        </nav>
        <div class="mt-auto p-4 border-t border-white/5">
           <button (click)="logout()" class="text-xs text-red-400 hover:text-red-300">Log Out</button>
        </div>
      </aside>

      <!-- Main -->
      <main class="flex-1 p-8 overflow-y-auto">
        
        <!-- DASHBOARD -->
        @if (tab() === 'DASHBOARD') {
          <h1 class="text-2xl font-bold mb-8">Dashboard Overview</h1>
          <div class="grid grid-cols-3 gap-6">
            <div class="p-6 rounded-xl bg-[#111] border border-white/5">
              <div class="text-zinc-500 text-sm mb-1">Total Users</div>
              <div class="text-3xl font-bold">12,450</div>
            </div>
            <div class="p-6 rounded-xl bg-[#111] border border-white/5">
               <div class="text-zinc-500 text-sm mb-1">Active Sessions</div>
              <div class="text-3xl font-bold text-green-400">843</div>
            </div>
             <div class="p-6 rounded-xl bg-[#111] border border-white/5">
               <div class="text-zinc-500 text-sm mb-1">Storage Used</div>
              <div class="text-3xl font-bold text-cyan-400">1.2 TB</div>
            </div>
          </div>
        }

        <!-- BLOG -->
        @if (tab() === 'BLOG') {
           <div class="flex justify-between items-center mb-8">
              <h1 class="text-2xl font-bold">Manage Blog Posts</h1>
              <button (click)="showBlogForm.set(true)" class="px-4 py-2 bg-cyan-600 rounded text-sm font-bold hover:bg-cyan-500">+ New Post</button>
           </div>

           <!-- List -->
           <div class="space-y-4">
             @for (post of posts(); track post.id) {
               <div class="flex items-center justify-between p-4 bg-[#111] rounded border border-white/5">
                 <div>
                    <h3 class="font-bold">{{ post.title }}</h3>
                    <div class="text-xs text-zinc-500">{{ post.date | date }} • {{ post.author }}</div>
                 </div>
                 <button (click)="deletePost(post.id)" class="text-red-400 text-sm hover:underline">Delete</button>
               </div>
             }
           </div>

           <!-- Create Modal -->
           @if (showBlogForm()) {
             <div class="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
               <div class="bg-[#15151A] p-6 rounded-xl w-full max-w-2xl border border-white/10 max-h-[90vh] overflow-y-auto">
                 <h2 class="text-xl font-bold mb-4">New Blog Post</h2>
                 <form [formGroup]="blogForm" (ngSubmit)="submitBlog()">
                    <div class="space-y-4">
                      <input formControlName="title" placeholder="Title" class="w-full bg-black border border-zinc-700 p-2 rounded text-white">
                      <input formControlName="category" placeholder="Category (e.g. Design)" class="w-full bg-black border border-zinc-700 p-2 rounded text-white">
                      <input formControlName="author" placeholder="Author" class="w-full bg-black border border-zinc-700 p-2 rounded text-white">
                      <input formControlName="image_url" placeholder="Image URL" class="w-full bg-black border border-zinc-700 p-2 rounded text-white">
                      <textarea formControlName="excerpt" placeholder="Short Excerpt" rows="2" class="w-full bg-black border border-zinc-700 p-2 rounded text-white"></textarea>
                      <textarea formControlName="content" placeholder="Content (HTML allowed)" rows="6" class="w-full bg-black border border-zinc-700 p-2 rounded text-white font-mono text-sm"></textarea>
                    </div>
                    <div class="flex justify-end gap-3 mt-6">
                      <button type="button" (click)="showBlogForm.set(false)" class="text-zinc-400 hover:text-white">Cancel</button>
                      <button type="submit" [disabled]="blogForm.invalid" class="px-6 py-2 bg-cyan-600 rounded text-white font-bold disabled:opacity-50">Publish</button>
                    </div>
                 </form>
               </div>
             </div>
           }
        }

        <!-- CAREERS -->
        @if (tab() === 'CAREERS') {
           <div class="flex justify-between items-center mb-8">
              <h1 class="text-2xl font-bold">Manage Careers</h1>
              <button (click)="showJobForm.set(true)" class="px-4 py-2 bg-purple-600 rounded text-sm font-bold hover:bg-purple-500">+ New Job</button>
           </div>

           <div class="space-y-4">
             @for (job of jobs(); track job.id) {
               <div class="flex items-center justify-between p-4 bg-[#111] rounded border border-white/5">
                 <div>
                    <h3 class="font-bold">{{ job.title }}</h3>
                    <div class="text-xs text-zinc-500">{{ job.department }} • {{ job.type }}</div>
                 </div>
                 <button (click)="deleteJob(job.id)" class="text-red-400 text-sm hover:underline">Delete</button>
               </div>
             }
           </div>

            <!-- Create Modal -->
           @if (showJobForm()) {
             <div class="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
               <div class="bg-[#15151A] p-6 rounded-xl w-full max-w-2xl border border-white/10">
                 <h2 class="text-xl font-bold mb-4">New Job Posting</h2>
                 <form [formGroup]="jobForm" (ngSubmit)="submitJob()">
                    <div class="space-y-4">
                      <input formControlName="title" placeholder="Job Title" class="w-full bg-black border border-zinc-700 p-2 rounded text-white">
                      <input formControlName="department" placeholder="Department" class="w-full bg-black border border-zinc-700 p-2 rounded text-white">
                      <input formControlName="location" placeholder="Location" class="w-full bg-black border border-zinc-700 p-2 rounded text-white">
                      <select formControlName="type" class="w-full bg-black border border-zinc-700 p-2 rounded text-white">
                        <option value="Full-time">Full-time</option>
                        <option value="Contract">Contract</option>
                        <option value="Part-time">Part-time</option>
                      </select>
                      <textarea formControlName="description" placeholder="Job Description" rows="4" class="w-full bg-black border border-zinc-700 p-2 rounded text-white"></textarea>
                    </div>
                    <div class="flex justify-end gap-3 mt-6">
                      <button type="button" (click)="showJobForm.set(false)" class="text-zinc-400 hover:text-white">Cancel</button>
                      <button type="submit" [disabled]="jobForm.invalid" class="px-6 py-2 bg-purple-600 rounded text-white font-bold disabled:opacity-50">Publish</button>
                    </div>
                 </form>
               </div>
             </div>
           }
        }

      </main>
    </div>
  `
})
export class AdminPanelComponent implements OnInit {
  auth = inject(AuthService);
  router = inject(Router);
  contentService = inject(ContentService);
  fb = inject(FormBuilder);

  tab = signal<AdminTab>('DASHBOARD');
  
  posts = signal<BlogPost[]>([]);
  jobs = signal<JobPost[]>([]);

  showBlogForm = signal(false);
  showJobForm = signal(false);

  blogForm: FormGroup;
  jobForm: FormGroup;

  constructor() {
    this.blogForm = this.fb.group({
      title: ['', Validators.required],
      category: ['', Validators.required],
      author: ['', Validators.required],
      image_url: ['', Validators.required],
      excerpt: ['', Validators.required],
      content: ['', Validators.required],
    });

    this.jobForm = this.fb.group({
      title: ['', Validators.required],
      department: ['', Validators.required],
      location: ['', Validators.required],
      type: ['Full-time', Validators.required],
      description: ['', Validators.required],
    });
  }

  ngOnInit() {
    this.loadContent();
  }

  loadContent() {
    this.contentService.getPosts().subscribe(p => this.posts.set(p));
    this.contentService.getJobs().subscribe(j => this.jobs.set(j));
  }

  submitBlog() {
    if (this.blogForm.valid) {
      this.contentService.createPost(this.blogForm.value).subscribe(() => {
        this.loadContent();
        this.showBlogForm.set(false);
        this.blogForm.reset();
      });
    }
  }

  deletePost(id: string) {
    if(confirm('Are you sure?')) {
      this.contentService.deletePost(id).subscribe(() => this.loadContent());
    }
  }

  submitJob() {
    if (this.jobForm.valid) {
      this.contentService.createJob(this.jobForm.value).subscribe(() => {
        this.loadContent();
        this.showJobForm.set(false);
        this.jobForm.reset();
      });
    }
  }

  deleteJob(id: string) {
    if(confirm('Are you sure?')) {
      this.contentService.deleteJob(id).subscribe(() => this.loadContent());
    }
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}