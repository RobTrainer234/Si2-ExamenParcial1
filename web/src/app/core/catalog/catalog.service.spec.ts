import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { CatalogService } from './catalog.service';

describe('CatalogService', () => {
  let service: CatalogService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(CatalogService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('sends catalog filters as query parameters', () => {
    service.list({ page: 2, page_size: 12, q: 'camisa', category_id: 3 }).subscribe((response) => expect(response.total).toBe(1));
    const request = http.expectOne((item) => item.url === '/api/v1/catalog');
    expect(request.request.params.get('q')).toBe('camisa');
    expect(request.request.params.get('category_id')).toBe('3');
    request.flush({ items: [], page: 2, page_size: 12, total: 1, total_pages: 1 });
  });

  it('requests availability with the selected variant', () => {
    service.availability(8, 4, 2).subscribe((items) => expect(items.length).toBe(1));
    const request = http.expectOne('/api/v1/catalog/8/availability?size_id=4&color_id=2');
    expect(request.request.method).toBe('GET');
    request.flush([{ branch_id: 1, branch_name: 'Centro', city_name: 'Santa Cruz', address: 'Centro 1', available: true, stock: 2 }]);
  });
});
