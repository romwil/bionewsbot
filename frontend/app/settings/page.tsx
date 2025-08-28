'use client';

import {
  Box,
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  Text,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  FormControl,
  FormLabel,
  Input,
  Select,
  Switch,
  Button,
  useToast,
  HStack,
  useColorModeValue,
  SimpleGrid,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  useDisclosure,
  InputGroup,
  InputRightElement,
  IconButton,
  FormHelperText,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import {
  FiSave,
  FiPlus,
  FiEdit,
  FiTrash2,
  FiEye,
  FiEyeOff,
  FiKey,
  FiUser,
  FiBell,
  FiDatabase,
  FiShield,
} from 'react-icons/fi';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsApi } from '@/lib/api/settings';
import { usersApi } from '@/lib/api/users';

export default function SettingsPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const cardBg = useColorModeValue('white', 'gray.800');
  const [showApiKey, setShowApiKey] = useState(false);

  // Forms
  const generalForm = useForm();
  const apiForm = useForm();
  const notificationForm = useForm();

  // Update settings mutation
  const updateSettingsMutation = useMutation({
    mutationFn: (data: any) => settingsApi.updateSettings(data),
    onSuccess: () => {
      toast({
        title: 'Settings updated',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    },
  });

  const handleGeneralSubmit = (data: any) => {
    updateSettingsMutation.mutate({ category: 'general', ...data });
  };

  const handleApiSubmit = (data: any) => {
    updateSettingsMutation.mutate({ category: 'api', ...data });
  };

  const handleNotificationSubmit = (data: any) => {
    updateSettingsMutation.mutate({ category: 'notifications', ...data });
  };

  return (
    <DashboardLayout>
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>Settings</Heading>
          <Text color="gray.600">Manage system configuration and preferences</Text>
        </Box>

        <Tabs colorScheme="brand" variant="enclosed">
          <TabList>
            <Tab><HStack><FiUser /><Text>General</Text></HStack></Tab>
            <Tab><HStack><FiKey /><Text>API Keys</Text></HStack></Tab>
            <Tab><HStack><FiBell /><Text>Notifications</Text></HStack></Tab>
            <Tab><HStack><FiShield /><Text>Users</Text></HStack></Tab>
          </TabList>

          <TabPanels>
            {/* General Settings */}
            <TabPanel>
              <Card bg={cardBg}>
                <CardHeader>
                  <Heading size="md">General Settings</Heading>
                </CardHeader>
                <CardBody>
                  <form onSubmit={generalForm.handleSubmit(handleGeneralSubmit)}>
                    <VStack spacing={4} align="stretch">
                      <FormControl>
                        <FormLabel>Company Name</FormLabel>
                        <Input
                          placeholder="Your company name"
                          {...generalForm.register('company_name')}
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel>Notification Email</FormLabel>
                        <Input
                          type="email"
                          placeholder="admin@example.com"
                          {...generalForm.register('notification_email')}
                        />
                      </FormControl>

                      <HStack spacing={4}>
                        <FormControl>
                          <FormLabel>Timezone</FormLabel>
                          <Select {...generalForm.register('timezone')}>
                            <option value="UTC">UTC</option>
                            <option value="America/New_York">Eastern Time</option>
                            <option value="America/Chicago">Central Time</option>
                            <option value="America/Los_Angeles">Pacific Time</option>
                          </Select>
                        </FormControl>

                        <FormControl>
                          <FormLabel>Language</FormLabel>
                          <Select {...generalForm.register('language')}>
                            <option value="en">English</option>
                            <option value="es">Spanish</option>
                            <option value="fr">French</option>
                          </Select>
                        </FormControl>
                      </HStack>

                      <Button
                        type="submit"
                        colorScheme="brand"
                        leftIcon={<FiSave />}
                        isLoading={updateSettingsMutation.isPending}
                      >
                        Save General Settings
                      </Button>
                    </VStack>
                  </form>
                </CardBody>
              </Card>
            </TabPanel>

            {/* API Keys */}
            <TabPanel>
              <Card bg={cardBg}>
                <CardHeader>
                  <Heading size="md">API Configuration</Heading>
                </CardHeader>
                <CardBody>
                  <Alert status="warning" mb={4}>
                    <AlertIcon />
                    <Text fontSize="sm">
                      API keys are encrypted and stored securely.
                    </Text>
                  </Alert>

                  <form onSubmit={apiForm.handleSubmit(handleApiSubmit)}>
                    <VStack spacing={4} align="stretch">
                      <FormControl>
                        <FormLabel>OpenAI API Key</FormLabel>
                        <InputGroup>
                          <Input
                            type={showApiKey ? 'text' : 'password'}
                            placeholder="sk-..."
                            {...apiForm.register('openai_api_key')}
                          />
                          <InputRightElement>
                            <IconButton
                              aria-label="Toggle visibility"
                              icon={showApiKey ? <FiEyeOff /> : <FiEye />}
                              size="sm"
                              variant="ghost"
                              onClick={() => setShowApiKey(!showApiKey)}
                            />
                          </InputRightElement>
                        </InputGroup>
                        <FormHelperText>Required for AI analysis</FormHelperText>
                      </FormControl>

                      <FormControl>
                        <FormLabel>News API Key</FormLabel>
                        <Input
                          type="password"
                          placeholder="Enter your News API key"
                          {...apiForm.register('news_api_key')}
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel>Rate Limit (requests/hour)</FormLabel>
                        <Input
                          type="number"
                          placeholder="100"
                          {...apiForm.register('rate_limit')}
                        />
                      </FormControl>

                      <Button
                        type="submit"
                        colorScheme="brand"
                        leftIcon={<FiSave />}
                        isLoading={updateSettingsMutation.isPending}
                      >
                        Save API Settings
                      </Button>
                    </VStack>
                  </form>
                </CardBody>
              </Card>
            </TabPanel>

            {/* Notifications */}
            <TabPanel>
              <Card bg={cardBg}>
                <CardHeader>
                  <Heading size="md">Notification Preferences</Heading>
                </CardHeader>
                <CardBody>
                  <form onSubmit={notificationForm.handleSubmit(handleNotificationSubmit)}>
                    <VStack spacing={4} align="stretch">
                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="email-alerts" mb="0">
                          Email Notifications
                        </FormLabel>
                        <Switch
                          id="email-alerts"
                          {...notificationForm.register('email_enabled')}
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel>Alert Threshold</FormLabel>
                        <Select {...notificationForm.register('alert_threshold')}>
                          <option value="low">Low - All alerts</option>
                          <option value="medium">Medium - Important alerts</option>
                          <option value="high">High - Critical alerts only</option>
                        </Select>
                      </FormControl>

                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="daily-digest" mb="0">
                          Daily Digest Email
                        </FormLabel>
                        <Switch
                          id="daily-digest"
                          {...notificationForm.register('daily_digest')}
                        />
                      </FormControl>

                      <Button
                        type="submit"
                        colorScheme="brand"
                        leftIcon={<FiSave />}
                        isLoading={updateSettingsMutation.isPending}
                      >
                        Save Notification Settings
                      </Button>
                    </VStack>
                  </form>
                </CardBody>
              </Card>
            </TabPanel>

            {/* Users */}
            <TabPanel>
              <Card bg={cardBg}>
                <CardHeader>
                  <HStack justify="space-between">
                    <Heading size="md">User Management</Heading>
                    <Button
                      size="sm"
                      colorScheme="brand"
                      leftIcon={<FiPlus />}
                    >
                      Add User
                    </Button>
                  </HStack>
                </CardHeader>
                <CardBody>
                  <TableContainer>
                    <Table variant="simple">
                      <Thead>
                        <Tr>
                          <Th>Name</Th>
                          <Th>Email</Th>
                          <Th>Role</Th>
                          <Th>Status</Th>
                          <Th>Actions</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        <Tr>
                          <Td>Admin User</Td>
                          <Td>admin@bionewsbot.com</Td>
                          <Td><Badge>Admin</Badge></Td>
                          <Td><Badge colorScheme="green">Active</Badge></Td>
                          <Td>
                            <HStack>
                              <IconButton
                                aria-label="Edit"
                                icon={<FiEdit />}
                                size="sm"
                                variant="ghost"
                              />
                              <IconButton
                                aria-label="Delete"
                                icon={<FiTrash2 />}
                                size="sm"
                                variant="ghost"
                                colorScheme="red"
                              />
                            </HStack>
                          </Td>
                        </Tr>
                      </Tbody>
                    </Table>
                  </TableContainer>
                </CardBody>
              </Card>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </VStack>
    </DashboardLayout>
  );
}
