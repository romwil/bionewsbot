'use client';

import {
  Flex,
  IconButton,
  HStack,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider,
  Text,
  useColorModeValue,
  FlexProps,
  Input,
  InputGroup,
  InputLeftElement,
  Badge,
  Box,
  VStack,
  useColorMode,
  Tooltip,
} from '@chakra-ui/react';
import {
  FiMenu,
  FiBell,
  FiSearch,
  FiMoon,
  FiSun,
} from 'react-icons/fi';
import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { wsClient } from '@/lib/utils/websocket';
import { Notification } from '@/types';

interface HeaderProps extends FlexProps {
  onOpen: () => void;
}

export function Header({ onOpen, ...rest }: HeaderProps) {
  const { colorMode, toggleColorMode } = useColorMode();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  
  const bgColor = useColorModeValue('white', 'gray.900');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    // Listen for real-time notifications
    const handleNotification = (notification: Notification) => {
      setNotifications(prev => [notification, ...prev].slice(0, 10));
      if (!notification.is_read) {
        setUnreadCount(prev => prev + 1);
      }
    };

    wsClient.on('notification', handleNotification);

    return () => {
      wsClient.off('notification', handleNotification);
    };
  }, []);

  const markAsRead = (notificationId: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  return (
    <Flex
      px={{ base: 4, md: 4 }}
      height="20"
      alignItems="center"
      bg={bgColor}
      borderBottomWidth="1px"
      borderBottomColor={borderColor}
      justifyContent={{ base: 'space-between', md: 'space-between' }}
      {...rest}
    >
      <IconButton
        display={{ base: 'flex', md: 'none' }}
        onClick={onOpen}
        variant="outline"
        aria-label="open menu"
        icon={<FiMenu />}
      />

      <HStack spacing={{ base: '2', md: '6' }} flex={1}>
        <InputGroup maxW="md" display={{ base: 'none', md: 'flex' }}>
          <InputLeftElement pointerEvents="none">
            <FiSearch color="gray.300" />
          </InputLeftElement>
          <Input
            type="text"
            placeholder="Search companies, insights..."
            variant="filled"
          />
        </InputGroup>
      </HStack>

      <HStack spacing={{ base: '2', md: '4' }}>
        <Tooltip label={`Switch to ${colorMode === 'light' ? 'dark' : 'light'} mode`}>
          <IconButton
            size="lg"
            variant="ghost"
            aria-label="Toggle color mode"
            icon={colorMode === 'light' ? <FiMoon /> : <FiSun />}
            onClick={toggleColorMode}
          />
        </Tooltip>

        <Menu>
          <MenuButton
            as={IconButton}
            size="lg"
            variant="ghost"
            aria-label="Notifications"
            icon={
              <Box position="relative">
                <FiBell />
                {unreadCount > 0 && (
                  <Badge
                    colorScheme="red"
                    position="absolute"
                    top="-1"
                    right="-1"
                    borderRadius="full"
                    fontSize="xs"
                  >
                    {unreadCount}
                  </Badge>
                )}
              </Box>
            }
          />
          <MenuList maxH="400px" overflowY="auto">
            <Text px="3" py="2" fontSize="sm" fontWeight="bold">
              Notifications
            </Text>
            <MenuDivider />
            {notifications.length === 0 ? (
              <MenuItem isDisabled>
                <Text fontSize="sm" color="gray.500">
                  No new notifications
                </Text>
              </MenuItem>
            ) : (
              notifications.map((notification) => (
                <MenuItem
                  key={notification.id}
                  onClick={() => markAsRead(notification.id)}
                  opacity={notification.is_read ? 0.6 : 1}
                >
                  <VStack align="start" spacing="1" w="full">
                    <HStack justify="space-between" w="full">
                      <Text fontSize="sm" fontWeight="medium">
                        {notification.title}
                      </Text>
                      <Badge
                        colorScheme={
                          notification.type === 'error' ? 'red' :
                          notification.type === 'warning' ? 'orange' :
                          notification.type === 'success' ? 'green' : 'blue'
                        }
                        fontSize="xs"
                      >
                        {notification.type}
                      </Badge>
                    </HStack>
                    <Text fontSize="xs" color="gray.500" noOfLines={2}>
                      {notification.message}
                    </Text>
                    <Text fontSize="xs" color="gray.400">
                      {format(new Date(notification.timestamp), 'MMM d, h:mm a')}
                    </Text>
                  </VStack>
                </MenuItem>
              ))
            )}
          </MenuList>
        </Menu>
      </HStack>
    </Flex>
  );
}
