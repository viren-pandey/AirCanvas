import { Routes } from '@angular/router';
import { LandingComponent } from './components/landing/landing.component';
import { LoginComponent } from './components/auth/login.component';
import { SignupComponent } from './components/auth/signup.component';
import { OnboardingComponent } from './components/auth/onboarding.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { ForgotPasswordComponent } from './components/auth/forgot-password.component';
import { CanvasComponent } from './components/canvas/canvas.component';
import { PricingComponent } from './components/pages/pricing.component';
import { BlogComponent } from './components/pages/blog.component';
import { CareersComponent } from './components/pages/careers.component';
import { AdminPanelComponent } from './components/admin/admin-panel.component';
import { FeaturesComponent } from './components/pages/features.component';
import { AboutComponent } from './components/pages/about.component';
import { ContactComponent } from './components/pages/contact.component';
import { TermsComponent } from './components/pages/terms.component';
import { PrivacyComponent } from './components/pages/privacy.component';
import { NotFoundComponent } from './components/pages/not-found.component';
import { CommunityComponent } from './components/dashboard/community.component';
import { SettingsComponent } from './components/dashboard/settings.component';
import { ProfileComponent } from './components/dashboard/profile.component';
import { inject } from '@angular/core';
import { AuthService } from './services/auth.service';

const authGuard = () => {
  const auth = inject(AuthService);
  return auth.isAuthenticated() || false;
};

const adminGuard = () => {
  const auth = inject(AuthService);
  return auth.isAdmin() || false;
};

export const routes: Routes = [
  { path: '', component: LandingComponent },
  { path: 'login', component: LoginComponent },
  { path: 'signup', component: SignupComponent },
  { path: 'forgot-password', component: ForgotPasswordComponent },
  { path: 'onboarding', component: OnboardingComponent },
  
  // Public Pages
  { path: 'pricing', component: PricingComponent },
  { path: 'blog', component: BlogComponent },
  { path: 'careers', component: CareersComponent },
  { path: 'features', component: FeaturesComponent },
  { path: 'about', component: AboutComponent },
  { path: 'contact', component: ContactComponent },
  { path: 'terms', component: TermsComponent },
  { path: 'privacy', component: PrivacyComponent },
  
  // App
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'community', component: CommunityComponent, canActivate: [authGuard] },
  { path: 'settings', component: SettingsComponent, canActivate: [authGuard] },
  { path: 'profile', component: ProfileComponent, canActivate: [authGuard] },
  { path: 'canvas', component: CanvasComponent, canActivate: [authGuard] },
  
  // Admin
  { path: 'admin-main', component: AdminPanelComponent, canActivate: [adminGuard] },
  
  // 404
  { path: '404', component: NotFoundComponent },
  { path: '**', component: NotFoundComponent } 
];