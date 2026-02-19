import { Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [RouterLink, ReactiveFormsModule, NgIf],
  template: `
    <div class="min-h-screen w-full flex items-center justify-center bg-[#030304] text-white p-6">
      
      <div class="w-full max-w-md reveal-up" style="animation-delay: 0.1s;">
        
        <div class="mb-12 text-center">
          <a routerLink="/" class="inline-block text-2xl font-display font-bold mb-8">AirCanvas</a>
          <h1 class="text-3xl font-display font-bold mb-2">Create your account</h1>
          <p class="text-zinc-500">Start your 14-day free trial. No credit card required.</p>
        </div>

        <form [formGroup]="signupForm" (ngSubmit)="onSubmit()" class="space-y-5">
          <div class="space-y-2">
            <label class="block text-sm font-medium text-zinc-400">Full Name</label>
            <input 
              type="text" 
              formControlName="name"
              class="w-full bg-[#0A0A0C] border border-zinc-800 rounded-lg px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-white focus:ring-1 focus:ring-white transition-all duration-300"
              placeholder="Jane Doe"
            >
          </div>

          <div class="space-y-2">
            <label class="block text-sm font-medium text-zinc-400">Email Address</label>
            <input 
              type="email" 
              formControlName="email"
              class="w-full bg-[#0A0A0C] border border-zinc-800 rounded-lg px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-white focus:ring-1 focus:ring-white transition-all duration-300"
              placeholder="name@company.com"
            >
          </div>

          <div class="space-y-2">
            <label class="block text-sm font-medium text-zinc-400">Password</label>
            <input 
              type="password" 
              formControlName="password"
              class="w-full bg-[#0A0A0C] border border-zinc-800 rounded-lg px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-white focus:ring-1 focus:ring-white transition-all duration-300"
              placeholder="Create a password"
            >
             <p class="text-xs text-zinc-600">Must be at least 8 characters.</p>
          </div>

          <div class="flex items-start gap-3 mt-6">
            <input type="checkbox" formControlName="terms" id="terms" class="mt-1 accent-white bg-zinc-900 border-zinc-700">
            <label for="terms" class="text-xs text-zinc-400 leading-relaxed">
              I agree to the <a href="#" class="text-white underline hover:text-zinc-300">Terms of Service</a> and <a href="#" class="text-white underline hover:text-zinc-300">Privacy Policy</a>.
            </label>
          </div>

          <button 
            type="submit" 
            [disabled]="signupForm.invalid || isSubmitting"
            class="w-full mt-4 py-4 rounded-lg bg-white text-black font-bold text-sm hover:bg-zinc-200 transition-all duration-300 transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isSubmitting ? 'Creating Account...' : 'Get Started' }}
          </button>

          @if (errorMessage) {
            <div class="text-sm text-red-400">{{ errorMessage }}</div>
          }
        </form>

        <p class="text-center mt-12 text-sm text-zinc-500">
          Already have an account? <a routerLink="/login" class="text-white hover:underline">Log in</a>
        </p>

      </div>
    </div>
  `
})
export class SignupComponent {
  fb = inject(FormBuilder);
  auth = inject(AuthService);
  router = inject(Router);

  signupForm = this.fb.group({
    name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    terms: [false, Validators.requiredTrue]
  });
  isSubmitting = false;
  errorMessage = '';

  onSubmit() {
    if (!this.signupForm.valid) {
      return;
    }

    this.errorMessage = '';
    this.isSubmitting = true;
    this.auth
      .signup(
        this.signupForm.value.name!,
        this.signupForm.value.email!,
        this.signupForm.value.password!,
      )
      .subscribe({
        next: () => {
          this.isSubmitting = false;
          this.router.navigate(['/onboarding']);
        },
        error: (err: unknown) => {
          this.isSubmitting = false;
          const message = err instanceof Error ? err.message : 'Unable to create account.';
          this.errorMessage = message;
        },
      });
  }
}
