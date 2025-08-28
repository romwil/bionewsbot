'use client';

import {
  Box,
  Grid,
  GridItem,
  Heading,
  Text,
  Card,
  CardBody,
  CardHeader,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  SimpleGrid,
  useColorModeValue,
  Spinner,
  Center,
  VStack,
  HStack,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Button,
  Icon,
} from '@chakra-ui/react';
import { useQuery } from '@tanstack/react-query';
import { FiTrendingUp, FiAlertCircle, FiActivity, FiDatabase } from 'react-icons/fi';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { InsightTrendChart } from './components/InsightTrendChart';
import { SentimentDistributionChart } from './components/SentimentDistributionChart';
import { RecentInsights } from './components/RecentInsights';
import { TopCompanies } from './components/TopCompanies';
import { insightsApi } from '@/lib/api/insights';
import { companiesApi } from '@/lib/api/companies';
import { DashboardMetrics } from '@/types';
import apiClient from '@/lib/api/client';

// Fetch dashboard metrics
const fetchDashboardMetrics = async (): Promise<DashboardMetrics> => {
  const response = await apiClient.get('/dashboard/metrics');
  return response.data;
};

export default function DashboardPage() {
  const cardBg = useColorModeValue('white', 'gray.800');
  
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: fetchDashboardMetrics,
    refetchInterval: 60000, // Refresh every minute
  });

  const { data: recentInsights, isLoading: insightsLoading } = useQuery({
    queryKey: ['recent-insights'],
    queryFn: () => insightsApi.getInsights({ limit: 5, sort_by: 'created_at', sort_order: 'desc' }),
  });

  const { data: topCompanies, isLoading: companiesLoading } = useQuery({
    queryKey: ['top-companies'],
    queryFn: () => companiesApi.getCompanies({ limit: 5, sort_by: 'insights_count', sort_order: 'desc' }),
  });

  if (metricsLoading || insightsLoading || companiesLoading) {
    return (
      <DashboardLayout>
        <Center h="50vh">
          <Spinner size="xl" color="brand.500" />
        </Center>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>Dashboard</Heading>
          <Text color="gray.600">Welcome to your life sciences intelligence hub</Text>
        </Box>

        {/* Metrics Cards */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Total Companies</StatLabel>
                <StatNumber>{metrics?.total_companies || 0}</StatNumber>
                <StatHelpText>
                  <HStack>
                    <Icon as={FiDatabase} />
                    <Text>{metrics?.active_companies || 0} active</Text>
                  </HStack>
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Total Insights</StatLabel>
                <StatNumber>{metrics?.total_insights || 0}</StatNumber>
                <StatHelpText>
                  <StatArrow type="increase" />
                  {metrics?.insights_today || 0} today
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Unread Insights</StatLabel>
                <StatNumber>{metrics?.unread_insights || 0}</StatNumber>
                <StatHelpText>
                  <HStack>
                    <Icon as={FiActivity} color="orange.500" />
                    <Text>Requires attention</Text>
                  </HStack>
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Flagged Insights</StatLabel>
                <StatNumber>{metrics?.flagged_insights || 0}</StatNumber>
                <StatHelpText>
                  <HStack>
                    <Icon as={FiAlertCircle} color="red.500" />
                    <Text>High priority</Text>
                  </HStack>
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Charts Row */}
        <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr' }} gap={6}>
          <GridItem>
            <Card bg={cardBg} h="full">
              <CardHeader>
                <Heading size="md">Insights Trend</Heading>
              </CardHeader>
              <CardBody>
                <InsightTrendChart />
              </CardBody>
            </Card>
          </GridItem>
          
          <GridItem>
            <Card bg={cardBg} h="full">
              <CardHeader>
                <Heading size="md">Sentiment Distribution</Heading>
              </CardHeader>
              <CardBody>
                <SentimentDistributionChart 
                  distribution={metrics?.sentiment_distribution || { positive: 0, negative: 0, neutral: 0 }}
                />
              </CardBody>
            </Card>
          </GridItem>
        </Grid>

        {/* Recent Activity Row */}
        <Grid templateColumns={{ base: '1fr', lg: '3fr 2fr' }} gap={6}>
          <GridItem>
            <Card bg={cardBg} h="full">
              <CardHeader>
                <HStack justify="space-between">
                  <Heading size="md">Recent Insights</Heading>
                  <Button size="sm" variant="ghost" as="a" href="/insights">
                    View All
                  </Button>
                </HStack>
              </CardHeader>
              <CardBody>
                <RecentInsights insights={recentInsights?.items || []} />
              </CardBody>
            </Card>
          </GridItem>
          
          <GridItem>
            <Card bg={cardBg} h="full">
              <CardHeader>
                <HStack justify="space-between">
                  <Heading size="md">Top Companies</Heading>
                  <Button size="sm" variant="ghost" as="a" href="/companies">
                    View All
                  </Button>
                </HStack>
              </CardHeader>
              <CardBody>
                <TopCompanies companies={topCompanies?.items || []} />
              </CardBody>
            </Card>
          </GridItem>
        </Grid>
      </VStack>
    </DashboardLayout>
  );
}
