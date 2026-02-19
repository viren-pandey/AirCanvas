import { Component } from '@angular/core';
import { NavbarComponent } from '../ui/navbar.component';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-privacy',
  standalone: true,
  imports: [NavbarComponent, CommonModule],
  template: `
    <app-navbar />
    <div class="min-h-screen bg-[#030304] text-white pt-32 pb-20">
      <div class="max-w-3xl mx-auto px-6">
        
        <h1 class="text-4xl font-display font-bold mb-8">Privacy Policy</h1>
        <p class="text-zinc-500 mb-12">Last updated: October 24, 2023</p>

        <div class="space-y-12 text-zinc-300 leading-relaxed">
          
          <section>
            <h2 class="text-xl font-bold text-white mb-4">1. Information We Collect</h2>
            <p>We collect information you provide directly to us, such as when you create an account, update your profile, or request customer support. We may also collect information created by your use of the AirCanvas services, such as gesture data and canvas metadata.</p>
          </section>

          <section>
            <h2 class="text-xl font-bold text-white mb-4">2. Camera Usage</h2>
            <p class="p-4 bg-zinc-900 border border-white/10 rounded-lg">
              <strong>Important:</strong> AirCanvas processes camera data locally on your device to interpret gestures. We do not store, record, or transmit video feeds to our servers.
            </p>
          </section>

          <section>
            <h2 class="text-xl font-bold text-white mb-4">3. How We Use Information</h2>
            <p>We use the information we collect to operate, maintain, and improve our services, such as to:</p>
            <ul class="list-disc pl-5 mt-4 space-y-2 text-zinc-400">
              <li>Provide and deliver the products and services you request.</li>
              <li>Send you technical notices, updates, security alerts, and support messages.</li>
              <li>Monitor and analyze trends, usage, and activities.</li>
            </ul>
          </section>

          <section>
            <h2 class="text-xl font-bold text-white mb-4">4. Data Security</h2>
            <p>We implement appropriate technical and organizational measures to protect the security of your personal information. However, please note that no system is completely secure.</p>
          </section>

        </div>

      </div>
    </div>
  `
})
export class PrivacyComponent {}