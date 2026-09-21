import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, vi } from 'vitest';

import { NotificationService } from './notification.service';

describe('NotificationService', () => {
  let service: NotificationService;

  beforeEach(() => {
    vi.useFakeTimers();
    TestBed.configureTestingModule({});
    service = TestBed.inject(NotificationService);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('publishes and expires transient notifications', () => {
    service.success('Saved');

    expect(service.messages()).toEqual([{ id: 1, kind: 'success', message: 'Saved' }]);

    vi.advanceTimersByTime(3800);

    expect(service.messages()).toEqual([]);
  });

  it('keeps only the latest notifications', () => {
    service.error('One');
    service.error('Two');
    service.error('Three');
    service.error('Four');
    service.error('Five');

    expect(service.messages().map((item) => item.message)).toEqual(['Two', 'Three', 'Four', 'Five']);
  });
});
