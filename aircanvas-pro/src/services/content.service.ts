import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';

export interface BlogPost {
  id: string;
  title: string;
  excerpt: string;
  content: string; // HTML allowed
  image_url: string;
  author: string;
  date: string;
  category: string;
}

export interface JobPost {
  id: string;
  title: string;
  department: string;
  location: string;
  type: string;
  description: string;
  date: string;
}

@Injectable({
  providedIn: 'root'
})
export class ContentService {
  private http = inject(HttpClient);
  // Set to true if running Python backend
  private USE_REAL_BACKEND = false; 
  private API_URL = 'http://localhost:8000/api';

  // Start with Empty Data (No Demo Content)
  private _posts = signal<BlogPost[]>([]);
  private _jobs = signal<JobPost[]>([]);

  // --- BLOGS ---
  getPosts(): Observable<BlogPost[]> {
    if (this.USE_REAL_BACKEND) return this.http.get<BlogPost[]>(`${this.API_URL}/posts`);
    return of(this._posts());
  }

  getPost(id: string): Observable<BlogPost | undefined> {
    if (this.USE_REAL_BACKEND) return this.http.get<BlogPost>(`${this.API_URL}/posts/${id}`);
    return of(this._posts().find(p => p.id === id));
  }

  createPost(post: Omit<BlogPost, 'id' | 'date'>): Observable<any> {
    if (this.USE_REAL_BACKEND) return this.http.post(`${this.API_URL}/posts`, post);
    
    const newPost = { ...post, id: crypto.randomUUID(), date: new Date().toISOString() };
    this._posts.update(posts => [newPost, ...posts]);
    return of(newPost);
  }

  deletePost(id: string): Observable<any> {
    if (this.USE_REAL_BACKEND) return this.http.delete(`${this.API_URL}/posts/${id}`);
    
    this._posts.update(posts => posts.filter(p => p.id !== id));
    return of(true);
  }

  // --- JOBS ---
  getJobs(): Observable<JobPost[]> {
    if (this.USE_REAL_BACKEND) return this.http.get<JobPost[]>(`${this.API_URL}/jobs`);
    return of(this._jobs());
  }

  createJob(job: Omit<JobPost, 'id' | 'date'>): Observable<any> {
    if (this.USE_REAL_BACKEND) return this.http.post(`${this.API_URL}/jobs`, job);
    
    const newJob = { ...job, id: crypto.randomUUID(), date: new Date().toISOString() };
    this._jobs.update(jobs => [newJob, ...jobs]);
    return of(newJob);
  }

  deleteJob(id: string): Observable<any> {
    if (this.USE_REAL_BACKEND) return this.http.delete(`${this.API_URL}/jobs/${id}`);
    
    this._jobs.update(jobs => jobs.filter(j => j.id !== id));
    return of(true);
  }
}