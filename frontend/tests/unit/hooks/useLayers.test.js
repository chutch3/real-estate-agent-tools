import { renderHook, act, waitFor } from '@testing-library/react';
import useLayers from '../../../src/hooks/useLayers';

const LOUISVILLE_BBOX = [-86.035, 37.997, -85.404, 38.375];

const MOCK_LAYERS_RESPONSE = {
  groups: [
    {
      id: 'crime',
      label: 'Crime',
      categories: [
        {
          id: 'crime-violent',
          label: 'Violent Crime',
          date_from: '2025-04-01',
          date_to: '2026-04-01',
          record_count: 10,
          bbox: LOUISVILLE_BBOX,
          tile_zoom: 12,
        },
        {
          id: 'crime-property',
          label: 'Property Crime',
          date_from: '2025-04-01',
          date_to: '2026-04-01',
          record_count: 20,
          bbox: LOUISVILLE_BBOX,
          tile_zoom: 12,
        },
      ],
    },
  ],
};

describe('useLayers', () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      json: () => Promise.resolve(MOCK_LAYERS_RESPONSE),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('fetches /layers without county_fips when countyFips is null', async () => {
    renderHook(() => useLayers(null));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.not.stringContaining('county_fips'),
    );
  });

  it('returns groups from API when countyFips is null', async () => {
    const { result } = renderHook(() => useLayers(null));

    await waitFor(() => {
      expect(result.current.groups).toHaveLength(1);
    });
  });

  it('fetches /layers with county_fips query param when countyFips is provided', async () => {
    renderHook(() => useLayers('21111'));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('county_fips=21111'),
      );
    });
  });

  it('re-fetches when countyFips changes', async () => {
    const { rerender } = renderHook(
      ({ countyFips }) => useLayers(countyFips),
      { initialProps: { countyFips: '21111' } },
    );

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

    rerender({ countyFips: '18019' });

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(2));
    expect(global.fetch).toHaveBeenLastCalledWith(
      expect.stringContaining('county_fips=18019'),
    );
  });

  it('returns groups from the API response', async () => {
    const { result } = renderHook(() => useLayers('21111'));

    await waitFor(() => {
      expect(result.current.groups).toHaveLength(1);
    });

    expect(result.current.groups[0].id).toBe('crime');
    expect(result.current.groups[0].categories).toHaveLength(2);
  });

  it('initializes all layers as inactive after fetching', async () => {
    const { result } = renderHook(() => useLayers('21111'));

    await waitFor(() => expect(result.current.groups).toHaveLength(1));

    expect(result.current.isActive('crime-violent')).toBe(false);
    expect(result.current.isActive('crime-property')).toBe(false);
  });

  it('toggle activates an inactive layer', async () => {
    const { result } = renderHook(() => useLayers('21111'));

    await waitFor(() => expect(result.current.groups).toHaveLength(1));

    act(() => result.current.toggle('crime-violent'));

    expect(result.current.isActive('crime-violent')).toBe(true);
  });

  it('toggle deactivates the active layer when clicked again', async () => {
    const { result } = renderHook(() => useLayers('21111'));

    await waitFor(() => expect(result.current.groups).toHaveLength(1));

    act(() => result.current.toggle('crime-violent'));
    expect(result.current.isActive('crime-violent')).toBe(true);

    act(() => result.current.toggle('crime-violent'));
    expect(result.current.isActive('crime-violent')).toBe(false);
  });

  it('toggle switches the active layer and deactivates the previous one', async () => {
    const { result } = renderHook(() => useLayers('21111'));

    await waitFor(() => expect(result.current.groups).toHaveLength(1));

    act(() => result.current.toggle('crime-violent'));
    expect(result.current.isActive('crime-violent')).toBe(true);
    expect(result.current.isActive('crime-property')).toBe(false);

    act(() => result.current.toggle('crime-property'));
    expect(result.current.isActive('crime-property')).toBe(true);
    expect(result.current.isActive('crime-violent')).toBe(false);
  });

  it('re-fetches without county_fips and clears active layers when countyFips becomes null', async () => {
    const { result, rerender } = renderHook(
      ({ countyFips }) => useLayers(countyFips),
      { initialProps: { countyFips: '21111' } },
    );

    await waitFor(() => expect(result.current.groups).toHaveLength(1));
    act(() => result.current.toggle('crime-violent'));
    expect(result.current.isActive('crime-violent')).toBe(true);

    rerender({ countyFips: null });

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(2));
    expect(global.fetch).toHaveBeenLastCalledWith(
      expect.not.stringContaining('county_fips'),
    );
    expect(result.current.isActive('crime-violent')).toBe(false);
  });
});
