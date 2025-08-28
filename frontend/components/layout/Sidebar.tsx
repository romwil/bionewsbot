'use client';

import {
  Box,
  CloseButton,
  Flex,
  Icon,
  Link,
  Text,
  VStack,
  Avatar,
  HStack,
  Divider,
  Button,
  useColorModeValue,
} from '@chakra-ui/react';
import {
  FiHome,
  FiTrendingUp,
  FiCompass,
  FiStar,
  FiSettings,
  FiUsers,
  FiBarChart2,
  FiLogOut,
} from 'react-icons/fi';
import { usePathname, useRouter } from 'next/navigation';
import NextLink from 'next/link';
import { useAuthStore } from '@/lib/store/useAuthStore';
import { IconType } from 'react-icons';

interface LinkItemProps {
  name: string;
  icon: IconType;
  href: string;
}

const LinkItems: Array<LinkItemProps> = [
  { name: 'Dashboard', icon: FiHome, href: '/dashboard' },
  { name: 'Companies', icon: FiCompass, href: '/companies' },
  { name: 'Insights', icon: FiTrendingUp, href: '/insights' },
  { name: 'Analysis', icon: FiBarChart2, href: '/analysis' },
  { name: 'Settings', icon: FiSettings, href: '/settings' },
];

interface SidebarProps {
  onClose: () => void;
  display?: object;
}

export function Sidebar({ onClose, ...rest }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();
  
  const bgColor = useColorModeValue('white', 'gray.900');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const handleLogout = async () => {
    await logout();
    router.push('/auth/login');
  };

  return (
    <Box
      transition="3s ease"
      bg={bgColor}
      borderRight="1px"
      borderRightColor={borderColor}
      w={{ base: 'full', md: 60 }}
      pos="fixed"
      h="full"
      {...rest}
    >
      <Flex h="20" alignItems="center" mx="8" justifyContent="space-between">
        <Text fontSize="2xl" fontWeight="bold" color="brand.500">
          BioNewsBot
        </Text>
        <CloseButton display={{ base: 'flex', md: 'none' }} onClick={onClose} />
      </Flex>
      
      <VStack spacing={0} align="stretch" flex={1}>
        {LinkItems.map((link) => {
          const isActive = pathname === link.href;
          return (
            <NavItem
              key={link.name}
              icon={link.icon}
              href={link.href}
              isActive={isActive}
            >
              {link.name}
            </NavItem>
          );
        })}
      </VStack>

      <Box p="4">
        <Divider mb="4" />
        {user && (
          <VStack spacing="4" align="stretch">
            <HStack spacing="3">
              <Avatar size="sm" name={user.name} />
              <Box flex="1">
                <Text fontSize="sm" fontWeight="medium">
                  {user.name}
                </Text>
                <Text fontSize="xs" color="gray.500">
                  {user.role}
                </Text>
              </Box>
            </HStack>
            <Button
              leftIcon={<FiLogOut />}
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              w="full"
              justifyContent="flex-start"
            >
              Logout
            </Button>
          </VStack>
        )}
      </Box>
    </Box>
  );
}

interface NavItemProps {
  icon: IconType;
  children: React.ReactNode;
  href: string;
  isActive: boolean;
}

const NavItem = ({ icon, children, href, isActive }: NavItemProps) => {
  const activeBg = useColorModeValue('brand.50', 'brand.900');
  const activeColor = useColorModeValue('brand.600', 'brand.200');
  const hoverBg = useColorModeValue('gray.100', 'gray.700');

  return (
    <Link
      as={NextLink}
      href={href}
      style={{ textDecoration: 'none' }}
      _focus={{ boxShadow: 'none' }}
    >
      <Flex
        align="center"
        p="4"
        mx="4"
        borderRadius="lg"
        role="group"
        cursor="pointer"
        bg={isActive ? activeBg : 'transparent'}
        color={isActive ? activeColor : 'inherit'}
        _hover={{
          bg: isActive ? activeBg : hoverBg,
        }}
      >
        {icon && (
          <Icon
            mr="4"
            fontSize="16"
            as={icon}
          />
        )}
        {children}
      </Flex>
    </Link>
  );
};
