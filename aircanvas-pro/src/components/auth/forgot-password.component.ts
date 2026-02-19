import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [RouterLink, ReactiveFormsModule, NgIf],
  template: `
    <div class="min-h-screen w-full flex items-center justify-center bg-[#030304] text-white p-6">
      
      <div class="w-full max-w-md reveal-up">
        
        <div class="mb-12 text-center">
          <a routerLink="/" class="inline-block text-2xl font-display font-bold mb-8">AirCanvas</a>
          
          @if (!submitted()) {
            <h1 class="text-3xl font-display font-bold mb-2">Reset Password</h1>
            <p class="text-zinc-500">Enter your email and we'll send you a link to reset your password.</p>
          } @else {
             <div class="w-16 h-16 bg-white rounded-full flex items-center justify-center mx-auto mb-6 text-black animate-pulse">
                <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
             </div>
             <h1 class="text-3xl font-display font-bold mb-2">Check your inbox</h1>
             <p class="text-zinc-500">We've sent a password reset link to <span class="text-white font-medium">{{ emailSentTo() }}</span>.</p>
          }
        </div>

        @if (!submitted()) {
          <form [formGroup]="forgotForm" (ngSubmit)="onSubmit()" class="space-y-6">
            <div class="space-y-2">
              <label class="block text-sm font-medium text-zinc-400">Email Address</label>
              <input 
                type="email" 
                formControlName="email"
                class="w-full bg-[#0A0A0C] border border-zinc-800 rounded-lg px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-white focus:ring-1 focus:ring-white transition-all duration-300"
                placeholder="name@company.com"
              >
              @if (forgotForm.get('email')?.touched && forgotForm.get('email')?.invalid) {
                  <span class="text-red-500 text-xs">Please enter a valid email.</span>
              }
            </div>

            <button 
              type="submit" 
              [disabled]="forgotForm.invalid"
              class="w-full py-4 rounded-lg bg-white text-black font-bold text-sm hover:bg-zinc-200 transition-all duration-300 transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send Reset Link
            </button>
          </form>
        } @else {
            <div class="space-y-4">
              <button 
                routerLink="/login"
                class="w-full py-4 rounded-lg bg-white text-black font-bold text-sm hover:bg-zinc-200 transition-all duration-300 transform active:scale-[0.98]"
              >
                Back to Sign In
              </button>
              
              <button 
                (click)="resend()"
                class="w-full py-4 rounded-lg border border-zinc-800 text-zinc-400 font-bold text-sm hover:text-white hover:border-zinc-600 transition-all duration-300"
              >
                Click to Resend
              </button>
            </div>
        }

        <p class="text-center mt-12 text-sm text-zinc-500">
          Remember your password? <a routerLink="/login" class="text-white hover:underline">Log in</a>
        </p>

      </div>
    </div>
  `
})
export class ForgotPasswordComponent {
  fb = inject(FormBuilder);
  submitted = signal(false);
  emailSentTo = signal('');

  forgotForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]]
  });

  onSubmit() {
    if (this.forgotForm.valid) {
      this.emailSentTo.set(this.forgotForm.value.email!);
      // Simulate API call delay for "Human" feel
      setTimeout(() => {
          this.submitted.set(true);
      }, 800);
    }
  }

  resend() {
     this.submitted.set(false);
  }
}