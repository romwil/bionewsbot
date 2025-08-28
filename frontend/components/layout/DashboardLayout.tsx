'use client';

import {
  Box,
  Drawer,
  DrawerContent,
  Flex,
  useDisclosure,
  useColorModeValue,
} from '@chakra-ui/react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { ProtectedRoute } from './ProtectedRoute';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const bgColor = useColorModeValue('gray.50', 'gray.900');

  return (
    <ProtectedRoute>
      <Box minH="100vh" bg={bgColor}>
        <Sidebar
          onClose={() => onClose}
          display={{ base: 'none', md: 'block' }}
        />
        <Drawer
          autoFocus={false}
          isOpen={isOpen}
          placement="left"
          onClose={onClose}
          returnFocusOnClose={false}
          onOverlayClick={onClose}
          size="full"
        >
          <DrawerContent>
            <Sidebar onClose={onClose} />
          </DrawerContent>
        </Drawer>
        
        <Box ml={{ base: 0, md: 60 }} transition=".3s ease">
          <Header onOpen={onOpen} />
          <Box as="main" p="4">
            {children}
          </Box>
        </Box>
      </Box>
    </ProtectedRoute>
  );
}
