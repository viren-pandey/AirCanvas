import { Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [RouterLink, ReactiveFormsModule, NgIf],
  template: `
    <div class="min-h-screen w-full flex items-center justify-center bg-[#030304] text-white p-6">
      
      <div class="w-full max-w-md reveal-up">
        
        <div class="mb-12 text-center">
          <a routerLink="/" class="inline-block text-2xl font-display font-bold mb-8">AirCanvas</a>
          <h1 class="text-3xl font-display font-bold mb-2">Welcome back</h1>
          <p class="text-zinc-500">Enter your details to access your workspace.</p>
        </div>

        <form [formGroup]="loginForm" (ngSubmit)="onSubmit()" class="space-y-6">
          <div class="space-y-2">
            <label class="block text-sm font-medium text-zinc-400">Email Address</label>
            <input 
              type="email" 
              formControlName="email"
              class="w-full bg-[#0A0A0C] border border-zinc-800 rounded-lg px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-white focus:ring-1 focus:ring-white transition-all duration-300"
              placeholder="name@company.com"
            >
             @if (loginForm.get('email')?.touched && loginForm.get('email')?.invalid) {
                <span class="text-red-500 text-xs">Please enter a valid email.</span>
             }
          </div>

          <div class="space-y-2">
            <div class="flex justify-between items-center">
              <label class="block text-sm font-medium text-zinc-400">Password</label>
              <a routerLink="/forgot-password" class="text-xs text-white hover:text-zinc-300 hover:underline">Forgot password?</a>
            </div>
            <input 
              type="password" 
              formControlName="password"
              class="w-full bg-[#0A0A0C] border border-zinc-800 rounded-lg px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-white focus:ring-1 focus:ring-white transition-all duration-300"
              placeholder="••••••••"
            >
          </div>

          <button 
            type="submit" 
            [disabled]="loginForm.invalid || isSubmitting"
            class="w-full py-4 rounded-lg bg-white text-black font-bold text-sm hover:bg-zinc-200 transition-all duration-300 transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isSubmitting ? 'Signing In...' : 'Sign In' }}
          </button>

          @if (errorMessage) {
            <div class="text-sm text-red-400">{{ errorMessage }}</div>
          }
        </form>

        <div class="my-8 flex items-center gap-4">
          <div class="h-px bg-zinc-800 flex-1"></div>
          <span class="text-xs text-zinc-600 font-mono">OR CONTINUE WITH</span>
          <div class="h-px bg-zinc-800 flex-1"></div>
        </div>

        <button class="w-full py-3 rounded-lg border border-zinc-800 bg-[#0A0A0C] text-white hover:bg-zinc-900 transition-colors flex items-center justify-center gap-3 text-sm font-medium">
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.536-6.033-5.652s2.701-5.652,6.033-5.652c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z"/></svg>
          Google
        </button>

        <p class="text-center mt-12 text-sm text-zinc-500">
          New to AirCanvas? <a routerLink="/signup" class="text-white hover:underline">Create an account</a>
        </p>

      </div>
    </div>
  `
})
export class LoginComponent {
  fb = inject(FormBuilder);
  auth = inject(AuthService);
  router = inject(Router);

  loginForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]]
  });
  isSubmitting = false;
  errorMessage = '';

  onSubmit() {
    if (!this.loginForm.valid) {
      return;
    }

    this.errorMessage = '';
    this.isSubmitting = true;
    this.auth.login(this.loginForm.value.email!, this.loginForm.value.password!).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err: unknown) => {
        this.isSubmitting = false;
        const message = err instanceof Error ? err.message : 'Unable to sign in.';
        this.errorMessage = message;
      },
    });
  }
}
