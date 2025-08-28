'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/lib/store/useAuthStore';
import { Center, Spinner } from '@chakra-ui/react';

const publicRoutes = ['/auth/login', '/auth/register'];

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, fetchUser } = useAuthStore();

  useEffect(() => {
    const checkAuth = async () => {
      if (!isAuthenticated && !publicRoutes.includes(pathname)) {
        router.push('/auth/login');
      } else if (isAuthenticated && publicRoutes.includes(pathname)) {
        router.push('/dashboard');
      }
    };

    checkAuth();
  }, [isAuthenticated, pathname, router]);

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <Center h="100vh">
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  // Don't render protected content if not authenticated
  if (!isAuthenticated && !publicRoutes.includes(pathname)) {
    return null;
  }

  return <>{children}</>;
}
