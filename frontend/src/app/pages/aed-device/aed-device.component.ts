// AED device record and incident report form (APP-45, 2026-11-21).
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, ElementRef, inject, OnInit, signal, viewChild } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { AED_CAMPAIGN_BRAND } from '@app/pages/aed-campaign/aed-campaign.brand';

import { SeoService } from '@app/services/seo.service';

interface AedDevice {
  aed_id: string;
  name: string;
  address: string;
  location_description: string;
  access: string;
  opening_hours: string;
  operational_status: string;
  operator_name: string;
  latitude: number | null;
  longitude: number | null;
  organization: { id: number; title: string };
  qr_url: string;
  report_types: { value: string; label: string }[];
}

const ACCESS_LABELS: Record<string, string> = {
  public: 'publiczny',
  customers: 'dla klientów obiektu',
  private: 'ograniczony',
  unknown: 'brak danych',
};

@Component({
  selector: 'app-aed-device',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './aed-device.component.html',
  styleUrls: ['../../shared/forms/forms.scss', './aed-device.component.scss'],
})
export class AedDeviceComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);
  private readonly seoService = inject(SeoService);
  private readonly fb = inject(FormBuilder);

  /** Mapa Serc identity (APP-58): ready logo files copied byte for byte from brand/logo; names from the campaign page. */
  readonly brand = {
    ...AED_CAMPAIGN_BRAND,
    logoSrc: '/assets/aed/mapa-serc-logo-kolor.svg',
    logoWithSloganSrc: '/assets/aed/mapa-serc-logo-haslo-kolor.svg',
    campaignLink: '/pl/aed',
  };

  readonly state = signal<'loading' | 'ready' | 'not-found' | 'error'>('loading');
  readonly device = signal<AedDevice | null>(null);
  readonly formOpen = signal(false);
  readonly submitting = signal(false);
  readonly submitError = signal<string | null>(null);
  readonly serverErrors = signal<Record<string, string[]>>({});
  readonly reportId = signal<number | null>(null);

  readonly formHeading = viewChild<ElementRef<HTMLElement>>('formHeading');
  readonly resultBox = viewChild<ElementRef<HTMLElement>>('resultBox');

  readonly form = this.fb.nonNullable.group({
    type: ['', Validators.required],
    description: ['', [Validators.required, Validators.maxLength(2000)]],
    reporter_name: ['', Validators.maxLength(200)], // optional: no personal data required (APP-60)
    contact: ['', Validators.maxLength(200)],
    consent: [false],
  });

  ngOnInit() {
    const aedId = this.route.snapshot.paramMap.get('aedId');
    this.seoService.setPageTitle('Defibrylator AED');
    this.http.get<{ data: AedDevice }>(`/api/aed/devices/${encodeURIComponent(aedId)}`).subscribe({
      next: (response) => {
        this.device.set(response.data);
        this.state.set('ready');
        this.seoService.setPageTitle(response.data.name);
        if (this.route.snapshot.queryParamMap.has('zglos')) {
          this.openForm();
        }
      },
      error: (error: HttpErrorResponse) => this.state.set(error.status === 404 ? 'not-found' : 'error'),
    });
  }

  accessLabel(value: string): string {
    return ACCESS_LABELS[value] || value;
  }

  mapUrl(device: AedDevice): string {
    return `https://www.openstreetmap.org/?mlat=${device.latitude}&mlon=${device.longitude}#map=18/${device.latitude}/${device.longitude}`;
  }

  openForm() {
    this.formOpen.set(true);
    setTimeout(() => this.formHeading()?.nativeElement.focus());
  }

  invalid(name: keyof typeof this.form.controls): boolean {
    const control = this.form.controls[name];
    return (control.touched && control.invalid) || !!this.serverErrors()[name];
  }

  consentMissing(): boolean {
    const { contact, consent } = this.form.getRawValue();
    return !!contact.trim() && !consent;
  }

  submit() {
    this.form.markAllAsTouched();
    this.serverErrors.set({});
    this.submitError.set(null);
    if (this.form.invalid || this.consentMissing()) {
      this.submitError.set('Formularz zawiera błędy. Popraw zaznaczone pola.');
      setTimeout(() => this.resultBox()?.nativeElement.focus());
      return;
    }
    const value = this.form.getRawValue();
    this.submitting.set(true);
    this.http
      .post<{ data: { id: number } }>(`/api/aed/devices/${this.device().aed_id}/reports`, {
        ...value,
        contact: value.contact.trim(),
        consent: !!value.contact.trim() && value.consent,
      })
      .subscribe({
        next: (response) => {
          this.submitting.set(false);
          this.reportId.set(response.data.id);
          this.form.reset();
          setTimeout(() => this.resultBox()?.nativeElement.focus());
        },
        error: (error: HttpErrorResponse) => {
          this.submitting.set(false);
          this.serverErrors.set(error.status === 400 && error.error?.errors ? error.error.errors : {});
          this.submitError.set(
            error.status === 400
              ? 'Formularz zawiera błędy. Popraw zaznaczone pola.'
              : 'Nie udało się wysłać zgłoszenia. Spróbuj ponownie za chwilę.',
          );
          setTimeout(() => this.resultBox()?.nativeElement.focus());
        },
      });
  }
}
