import { Component } from '@angular/core';
import { NavbarComponent } from '../ui/navbar.component';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-terms',
  standalone: true,
  imports: [NavbarComponent, CommonModule],
  template: `
    <app-navbar />
    <div class="min-h-screen bg-[#030304] text-white pt-32 pb-20">
      <div class="max-w-3xl mx-auto px-6">
        
        <h1 class="text-4xl font-display font-bold mb-8">Terms of Service</h1>
        <p class="text-zinc-500 mb-12">Last updated: October 24, 2023</p>

        <div class="space-y-12 text-zinc-300 leading-relaxed">
          
          <section>
            <h2 class="text-xl font-bold text-white mb-4">1. Acceptance of Terms</h2>
            <p>By accessing and using AirCanvas, you accept and agree to be bound by the terms and provision of this agreement. In addition, when using these particular services, you shall be subject to any posted guidelines or rules applicable to such services.</p>
          </section>

          <section>
            <h2 class="text-xl font-bold text-white mb-4">2. Description of Service</h2>
            <p>AirCanvas provides users with a gesture-controlled drawing interface. You are responsible for obtaining access to the Service and that access may involve third party fees (such as Internet service provider or airtime charges).</p>
          </section>

          <section>
            <h2 class="text-xl font-bold text-white mb-4">3. User Conduct</h2>
            <p>You agree to not use the Service to:</p>
            <ul class="list-disc pl-5 mt-4 space-y-2 text-zinc-400">
              <li>Upload any content that is unlawful, harmful, threatening, or abusive.</li>
              <li>Impersonate any person or entity.</li>
              <li>Forge headers or otherwise manipulate identifiers.</li>
            </ul>
          </section>

          <section>
            <h2 class="text-xl font-bold text-white mb-4">4. Intellectual Property</h2>
            <p>The Service and its original content, features, and functionality are and will remain the exclusive property of AirCanvas Inc and its licensors. The Service is protected by copyright, trademark, and other laws.</p>
          </section>

        </div>

      </div>
    </div>
  `
})
export class TermsComponent {}