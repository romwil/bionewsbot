'use client';

import { ChakraProvider } from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState, useEffect } from 'react';
import theme from '@/lib/theme';
import { wsClient } from '@/lib/utils/websocket';
import { useAuthStore } from '@/lib/store/useAuthStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  const [isClient, setIsClient] = useState(false);
  const { isAuthenticated, fetchUser } = useAuthStore();

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    // Fetch user on mount if authenticated
    if (isAuthenticated) {
      fetchUser();
      // Connect WebSocket
      wsClient.connect();
    }

    return () => {
      wsClient.disconnect();
    };
  }, [isAuthenticated, fetchUser]);

  if (!isClient) {
    return null;
  }

  return (
    <ChakraProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        {children}
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ChakraProvider>
  );
}
