import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { NgClass } from '@angular/common';

@Component({
  selector: 'app-onboarding',
  standalone: true,
  imports: [NgClass],
  template: `
    <div class="min-h-screen w-full flex items-center justify-center bg-[#0B0F1A] p-6">
      <div class="w-full max-w-2xl">
        
        <!-- Progress -->
        <div class="flex items-center justify-between mb-12 px-4">
           <div class="flex gap-2">
             <div class="h-1 w-12 rounded-full" [ngClass]="step() >= 1 ? 'bg-cyan-500' : 'bg-white/10'"></div>
             <div class="h-1 w-12 rounded-full" [ngClass]="step() >= 2 ? 'bg-cyan-500' : 'bg-white/10'"></div>
             <div class="h-1 w-12 rounded-full" [ngClass]="step() >= 3 ? 'bg-cyan-500' : 'bg-white/10'"></div>
           </div>
           <span class="text-gray-500 text-sm">Step {{step()}} of 3</span>
        </div>

        <!-- Step 1: Mode -->
        @if (step() === 1) {
          <div class="animate-fade-in">
            <h1 class="text-3xl md:text-4xl font-display font-bold mb-4">Choose your interaction style</h1>
            <p class="text-gray-400 mb-8">How do you prefer to control your canvas?</p>

            <div class="grid md:grid-cols-2 gap-4">
              <button (click)="selectMode('gesture')" 
                class="p-6 rounded-2xl border-2 text-left transition-all hover:scale-[1.02]"
                [ngClass]="selectedMode() === 'gesture' ? 'border-cyan-500 bg-cyan-500/10' : 'border-white/10 bg-white/5 hover:border-white/30'">
                <div class="w-12 h-12 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center mb-4">
                  <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11" /></svg>
                </div>
                <h3 class="text-lg font-bold mb-1">Gesture Priority</h3>
                <p class="text-sm text-gray-400">Full hand tracking enabled. Best for expressive drawing.</p>
              </button>

              <button (click)="selectMode('voice')" 
                class="p-6 rounded-2xl border-2 text-left transition-all hover:scale-[1.02]"
                [ngClass]="selectedMode() === 'voice' ? 'border-purple-500 bg-purple-500/10' : 'border-white/10 bg-white/5 hover:border-white/30'">
                <div class="w-12 h-12 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center mb-4">
                  <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                </div>
                <h3 class="text-lg font-bold mb-1">Voice Priority</h3>
                <p class="text-sm text-gray-400">Commands and macros. Best for precision and speed.</p>
              </button>
            </div>
            
             <div class="mt-8 flex justify-end">
              <button (click)="nextStep()" [disabled]="!selectedMode()" class="px-8 py-3 bg-white text-black font-bold rounded-xl hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">Continue</button>
            </div>
          </div>
        }

        <!-- Step 2: Theme -->
        @if (step() === 2) {
           <div class="animate-fade-in">
            <h1 class="text-3xl md:text-4xl font-display font-bold mb-4">Set your vibe</h1>
            <p class="text-gray-400 mb-8">Choose a workspace theme.</p>

            <div class="grid grid-cols-3 gap-4">
              <button (click)="selectTheme('cyber')" class="group relative rounded-2xl overflow-hidden aspect-video border-2 transition-all" [ngClass]="selectedTheme() === 'cyber' ? 'border-cyan-500' : 'border-transparent'">
                <div class="absolute inset-0 bg-[#0B0F1A]"></div>
                <div class="absolute inset-0 flex items-center justify-center font-bold text-gray-300 z-10">Cyber Dark</div>
                 <div class="absolute bottom-0 left-0 w-full h-1 bg-cyan-500"></div>
              </button>
              
               <button (click)="selectTheme('studio')" class="group relative rounded-2xl overflow-hidden aspect-video border-2 transition-all" [ngClass]="selectedTheme() === 'studio' ? 'border-white' : 'border-transparent'">
                <div class="absolute inset-0 bg-[#1a1a1a]"></div>
                <div class="absolute inset-0 flex items-center justify-center font-bold text-gray-300 z-10">Studio Gray</div>
                 <div class="absolute bottom-0 left-0 w-full h-1 bg-gray-500"></div>
              </button>
              
               <button (click)="selectTheme('neon')" class="group relative rounded-2xl overflow-hidden aspect-video border-2 transition-all" [ngClass]="selectedTheme() === 'neon' ? 'border-purple-500' : 'border-transparent'">
                <div class="absolute inset-0 bg-[#050510]"></div>
                 <div class="absolute top-0 right-0 w-20 h-20 bg-purple-600 blur-[40px]"></div>
                <div class="absolute inset-0 flex items-center justify-center font-bold text-gray-300 z-10">Neon Nights</div>
                <div class="absolute bottom-0 left-0 w-full h-1 bg-purple-500"></div>
              </button>
            </div>

            <div class="mt-8 flex justify-between">
              <button (click)="prevStep()" class="text-gray-400 hover:text-white">Back</button>
              <button (click)="nextStep()" [disabled]="!selectedTheme()" class="px-8 py-3 bg-white text-black font-bold rounded-xl hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">Continue</button>
            </div>
           </div>
        }
        
        <!-- Step 3: Success -->
        @if (step() === 3) {
           <div class="animate-fade-in text-center">
             <div class="w-24 h-24 rounded-full bg-green-500/20 mx-auto flex items-center justify-center text-green-500 mb-6">
               <svg class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
             </div>
             <h1 class="text-3xl font-bold mb-4">You're all set!</h1>
             <p class="text-gray-400 mb-8">AirCanvas is configured and ready for your first masterpiece.</p>
             
             <button (click)="finish()" class="px-10 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full text-white font-bold shadow-lg shadow-cyan-500/30 hover:scale-105 transition-transform">
               Launch Dashboard
             </button>
           </div>
        }

      </div>
    </div>
  `
})
export class OnboardingComponent {
  auth = inject(AuthService);
  router = inject(Router);
  
  step = signal(1);
  selectedMode = signal<string | null>(null);
  selectedTheme = signal<string | null>(null);

  selectMode(mode: string) {
    this.selectedMode.set(mode);
  }

  selectTheme(theme: string) {
    this.selectedTheme.set(theme);
  }

  nextStep() {
    this.step.update(s => s + 1);
  }

  prevStep() {
    this.step.update(s => s - 1);
  }

  finish() {
    this.auth.updateProfile({ 
      mode: this.selectedMode()!, 
      theme: this.selectedTheme()! 
    });
    this.router.navigate(['/dashboard']);
  }
}