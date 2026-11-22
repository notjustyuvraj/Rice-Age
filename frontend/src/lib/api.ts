import type { DashboardSummary, PaginatedScans, ScanDetail, User } from './types';
import { filterScans, mockAsset, mockScan, mockSummary, mockUser } from './mockData';

const TOKEN_KEY = 'grain_analyzer_token';

export const getToken = () => sessionStorage.getItem(TOKEN_KEY);
export const setToken = (token: string | null) => token ? sessionStorage.setItem(TOKEN_KEY, token) : sessionStorage.removeItem(TOKEN_KEY);

export const api = {
  login: async (email: string, password: string) => {
    if (!email.trim() || !password.trim()) throw new Error('Enter an email address and password.');
    sessionStorage.setItem('grain_analyzer_email', email.trim());
    return { access_token: 'mock-session', token_type: 'bearer', expires_in: 60 * 60 * 8 };
  },
  me: async (): Promise<User> => {
    if (!getToken()) throw new Error('Not signed in');
    return { ...mockUser, email: sessionStorage.getItem('grain_analyzer_email') || mockUser.email };
  },
  summary: async (): Promise<DashboardSummary> => mockSummary(),
  latest: async () => ({ item: mockSummary().latest_scan }),
  scans: async (params: URLSearchParams): Promise<PaginatedScans> => filterScans(params),
  scan: async (id: number): Promise<ScanDetail> => {
    const scan = mockScan(id);
    if (!scan) throw new Error('Scan not found');
    return scan;
  },
  departments: async () => mockSummary().departments.map(department => ({ ...department, location: null })),
  asset: async (path: string) => URL.createObjectURL(mockAsset(path)),
};
