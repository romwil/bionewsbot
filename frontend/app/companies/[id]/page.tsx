'use client';

import {
  Box,
  Card,
  CardBody,
  CardHeader,
  Heading,
  VStack,
  Text,
  HStack,
  Badge,
  Button,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useColorModeValue,
  Spinner,
  Center,
  Link,
  IconButton,
  useToast,
  Divider,
} from '@chakra-ui/react';
import {
  FiEdit,
  FiExternalLink,
  FiTrendingUp,
  FiFileText,
  FiAlertCircle,
  FiActivity,
  FiArrowLeft,
} from 'react-icons/fi';
import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { RecentInsights } from '@/components/dashboard/RecentInsights';
import { companiesApi } from '@/lib/api/companies';
import { insightsApi } from '@/lib/api/insights';
import { format } from 'date-fns';
import NextLink from 'next/link';

export default function CompanyDetailPage() {
  const params = useParams();
  const router = useRouter();
  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');
  const companyId = params.id as string;

  // Fetch company details
  const { data: company, isLoading } = useQuery({
    queryKey: ['company', companyId],
    queryFn: () => companiesApi.getCompany(companyId),
  });

  // Fetch company insights
  const { data: insights } = useQuery({
    queryKey: ['company-insights', companyId],
    queryFn: () => insightsApi.getInsights({ company_id: companyId }),
  });

  // Fetch company stats
  const { data: stats } = useQuery({
    queryKey: ['company-stats', companyId],
    queryFn: () => companiesApi.getCompanyStats(companyId),
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'green';
      case 'paused':
        return 'orange';
      case 'archived':
        return 'gray';
      default:
        return 'gray';
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <Center py={20}>
          <Spinner size="xl" color="brand.500" />
        </Center>
      </DashboardLayout>
    );
  }

  if (!company) {
    return (
      <DashboardLayout>
        <Center py={20}>
          <VStack>
            <Text color="gray.500">Company not found</Text>
            <Button onClick={() => router.push('/companies')}>Back to Companies</Button>
          </VStack>
        </Center>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Button
            variant="ghost"
            leftIcon={<FiArrowLeft />}
            onClick={() => router.push('/companies')}
            mb={4}
          >
            Back to Companies
          </Button>
          
          <HStack justify="space-between" align="start">
            <Box>
              <HStack spacing={3} mb={2}>
                <Heading size="lg">{company.name}</Heading>
                {company.ticker && (
                  <Badge colorScheme="purple" fontSize="md">
                    {company.ticker}
                  </Badge>
                )}
                <Badge colorScheme={getStatusColor(company.monitoring_status)} fontSize="sm">
                  {company.monitoring_status}
                </Badge>
              </HStack>
              <Text color="gray.600">{company.industry}</Text>
            </Box>
            
            <HStack>
              {company.website && (
                <IconButton
                  as="a"
                  href={company.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Visit website"
                  icon={<FiExternalLink />}
                  variant="ghost"
                />
              )}
              <Button
                leftIcon={<FiEdit />}
                onClick={() => router.push(`/companies/${companyId}/edit`)}
              >
                Edit Company
              </Button>
            </HStack>
          </HStack>
        </Box>

        {/* Stats Cards */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Total Insights</StatLabel>
                <StatNumber>{stats?.total_insights || 0}</StatNumber>
                <StatHelpText>
                  <HStack spacing={1}>
                    <FiFileText />
                    <Text>All time</Text>
                  </HStack>
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Recent Activity</StatLabel>
                <StatNumber>{stats?.recent_insights || 0}</StatNumber>
                <StatHelpText>
                  <HStack spacing={1}>
                    <FiActivity />
                    <Text>Last 7 days</Text>
                  </HStack>
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Sentiment Score</StatLabel>
                <StatNumber>{stats?.sentiment_score || 'N/A'}</StatNumber>
                <StatHelpText>
                  <HStack spacing={1}>
                    <FiTrendingUp />
                    <Text>Average</Text>
                  </HStack>
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Alerts</StatLabel>
                <StatNumber color="orange.500">{stats?.active_alerts || 0}</StatNumber>
                <StatHelpText>
                  <HStack spacing={1}>
                    <FiAlertCircle />
                    <Text>Active</Text>
                  </HStack>
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Tabs */}
        <Card bg={cardBg}>
          <CardBody>
            <Tabs colorScheme="brand">
              <TabList>
                <Tab>Overview</Tab>
                <Tab>Recent Insights</Tab>
                <Tab>Analytics</Tab>
                <Tab>Configuration</Tab>
              </TabList>

              <TabPanels>
                {/* Overview Tab */}
                <TabPanel>
                  <VStack align="stretch" spacing={4}>
                    {company.description && (
                      <Box>
                        <Text fontWeight="bold" mb={2}>Description</Text>
                        <Text>{company.description}</Text>
                      </Box>
                    )}
                    
                    <Divider />
                    
                    <SimpleGrid columns={2} spacing={4}>
                      <Box>
                        <Text fontWeight="bold" mb={2}>Company Information</Text>
                        <VStack align="stretch" spacing={2}>
                          <HStack justify="space-between">
                            <Text fontSize="sm" color="gray.600">Industry:</Text>
                            <Text fontSize="sm">{company.industry}</Text>
                          </HStack>
                          {company.website && (
                            <HStack justify="space-between">
                              <Text fontSize="sm" color="gray.600">Website:</Text>
                              <Link
                                href={company.website}
                                isExternal
                                color="brand.500"
                                fontSize="sm"
                              >
                                {company.website}
                              </Link>
                            </HStack>
                          )}
                          <HStack justify="space-between">
                            <Text fontSize="sm" color="gray.600">Added:</Text>
                            <Text fontSize="sm">
                              {format(new Date(company.created_at), 'MMM d, yyyy')}
                            </Text>
                          </HStack>
                        </VStack>
                      </Box>
                      
                      <Box>
                        <Text fontWeight="bold" mb={2}>Monitoring Status</Text>
                        <VStack align="stretch" spacing={2}>
                          <HStack justify="space-between">
                            <Text fontSize="sm" color="gray.600">Status:</Text>
                            <Badge colorScheme={getStatusColor(company.monitoring_status)}>
                              {company.monitoring_status}
                            </Badge>
                          </HStack>
                          <HStack justify="space-between">
                            <Text fontSize="sm" color="gray.600">Last Updated:</Text>
                            <Text fontSize="sm">
                              {format(new Date(company.updated_at), 'MMM d, yyyy')}
                            </Text>
                          </HStack>
                        </VStack>
                      </Box>
                    </SimpleGrid>
                  </VStack>
                </TabPanel>

                {/* Recent Insights Tab */}
                <TabPanel>
                  {insights && insights.items.length > 0 ? (
                    <RecentInsights insights={insights.items} />
                  ) : (
                    <Center py={10}>
                      <Text color="gray.500">No insights found for this company</Text>
                    </Center>
                  )}
                </TabPanel>

                {/* Analytics Tab */}
                <TabPanel>
                  <Center py={10}>
                    <VStack>
                      <Text color="gray.500">Analytics coming soon</Text>
                      <Text fontSize="sm" color="gray.400">
                        Charts and trends for this company will appear here
                      </Text>
                    </VStack>
                  </Center>
                </TabPanel>

                {/* Configuration Tab */}
                <TabPanel>
                  <VStack align="stretch" spacing={4}>
                    <Box>
                      <Text fontWeight="bold" mb={2}>Monitoring Configuration</Text>
                      <Text fontSize="sm" color="gray.600">
                        Configure specific monitoring settings for this company
                      </Text>
                    </Box>
                    
                    <Button colorScheme="brand" variant="outline">
                      Configure Alerts
                    </Button>
                  </VStack>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </CardBody>
        </Card>
      </VStack>
    </DashboardLayout>
  );
}
