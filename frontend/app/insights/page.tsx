'use client';

import {
  Box,
  Card,
  CardBody,
  CardHeader,
  Heading,
  HStack,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Text,
  VStack,
  SimpleGrid,
  Badge,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useColorModeValue,
  Spinner,
  Center,
  Button,
  Flex,
  useToast,
  Link,
  Icon,
} from '@chakra-ui/react';
import {
  FiSearch,
  FiFilter,
  FiRefreshCw,
  FiExternalLink,
  FiBookmark,
  FiFlag,
  FiMoreVertical,
  FiEye,
} from 'react-icons/fi';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { InsightDetailModal } from './components/InsightDetailModal';
import { insightsApi } from '@/lib/api/insights';
import { Insight } from '@/types';
import { format } from 'date-fns';
import NextLink from 'next/link';

export default function InsightsPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [sentimentFilter, setSentimentFilter] = useState('all');
  const [flaggedFilter, setFlaggedFilter] = useState('all');
  const [selectedInsight, setSelectedInsight] = useState<Insight | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // Fetch insights
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['insights', searchTerm, typeFilter, sentimentFilter, flaggedFilter],
    queryFn: () => insightsApi.getInsights({
      search: searchTerm,
      type: typeFilter !== 'all' ? typeFilter : undefined,
      sentiment: sentimentFilter !== 'all' ? sentimentFilter : undefined,
      is_flagged: flaggedFilter === 'flagged' ? true : flaggedFilter === 'unflagged' ? false : undefined,
    }),
  });

  // Mark as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: (id: string) => insightsApi.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['insights'] });
    },
  });

  // Toggle flag mutation
  const toggleFlagMutation = useMutation({
    mutationFn: ({ id, flagged }: { id: string; flagged: boolean }) => 
      insightsApi.updateInsight(id, { is_flagged: flagged }),
    onSuccess: () => {
      toast({
        title: 'Insight updated',
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
      queryClient.invalidateQueries({ queryKey: ['insights'] });
    },
  });

  const handleViewDetail = (insight: Insight) => {
    setSelectedInsight(insight);
    setIsDetailOpen(true);
    if (!insight.is_read) {
      markAsReadMutation.mutate(insight.id);
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'green';
      case 'negative':
        return 'red';
      case 'neutral':
        return 'gray';
      default:
        return 'gray';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'news':
        return 'blue';
      case 'financial':
        return 'purple';
      case 'regulatory':
        return 'orange';
      case 'clinical':
        return 'teal';
      case 'partnership':
        return 'cyan';
      case 'product':
        return 'pink';
      default:
        return 'gray';
    }
  };

  return (
    <DashboardLayout>
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>Insights</Heading>
          <Text color="gray.600">Monitor and analyze life sciences intelligence</Text>
        </Box>

        {/* Filters */}
        <Card bg={cardBg}>
          <CardBody>
            <Flex wrap="wrap" gap={4}>
              <InputGroup maxW="md">
                <InputLeftElement pointerEvents="none">
                  <FiSearch color="gray.300" />
                </InputLeftElement>
                <Input
                  placeholder="Search insights..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </InputGroup>
              
              <Select
                maxW="200px"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <option value="all">All Types</option>
                <option value="news">News</option>
                <option value="financial">Financial</option>
                <option value="regulatory">Regulatory</option>
                <option value="clinical">Clinical</option>
                <option value="partnership">Partnership</option>
                <option value="product">Product</option>
              </Select>
              
              <Select
                maxW="200px"
                value={sentimentFilter}
                onChange={(e) => setSentimentFilter(e.target.value)}
              >
                <option value="all">All Sentiments</option>
                <option value="positive">Positive</option>
                <option value="negative">Negative</option>
                <option value="neutral">Neutral</option>
              </Select>
              
              <Select
                maxW="200px"
                value={flaggedFilter}
                onChange={(e) => setFlaggedFilter(e.target.value)}
              >
                <option value="all">All Insights</option>
                <option value="flagged">Flagged Only</option>
                <option value="unflagged">Unflagged Only</option>
              </Select>
              
              <IconButton
                aria-label="Refresh"
                icon={<FiRefreshCw />}
                variant="ghost"
                onClick={() => refetch()}
              />
            </Flex>
          </CardBody>
        </Card>

        {/* Insights Grid */}
        {isLoading ? (
          <Center py={10}>
            <Spinner size="xl" color="brand.500" />
          </Center>
        ) : (
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
            {data?.items.map((insight) => (
              <Card
                key={insight.id}
                bg={cardBg}
                borderWidth="1px"
                borderColor={borderColor}
                _hover={{ shadow: 'md' }}
                transition="all 0.2s"
                opacity={insight.is_read ? 0.8 : 1}
              >
                <CardBody>
                  <VStack align="stretch" spacing={3}>
                    <HStack justify="space-between">
                      <HStack spacing={2}>
                        <Badge colorScheme={getTypeColor(insight.type)} size="sm">
                          {insight.type}
                        </Badge>
                        <Badge colorScheme={getSentimentColor(insight.sentiment)} size="sm">
                          {insight.sentiment}
                        </Badge>
                        {insight.is_flagged && (
                          <Badge colorScheme="red" variant="solid" size="sm">
                            Flagged
                          </Badge>
                        )}
                      </HStack>
                      <Menu>
                        <MenuButton
                          as={IconButton}
                          icon={<FiMoreVertical />}
                          variant="ghost"
                          size="sm"
                        />
                        <MenuList>
                          <MenuItem
                            icon={<FiEye />}
                            onClick={() => handleViewDetail(insight)}
                          >
                            View Details
                          </MenuItem>
                          <MenuItem
                            icon={<FiFlag />}
                            onClick={() => toggleFlagMutation.mutate({
                              id: insight.id,
                              flagged: !insight.is_flagged,
                            })}
                          >
                            {insight.is_flagged ? 'Unflag' : 'Flag'}
                          </MenuItem>
                          <MenuItem
                            icon={<FiExternalLink />}
                            as="a"
                            href={insight.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            View Source
                          </MenuItem>
                        </MenuList>
                      </Menu>
                    </HStack>
                    
                    <Box>
                      <Text fontWeight="bold" fontSize="md" noOfLines={2}>
                        {insight.title}
                      </Text>
                      <Text fontSize="sm" color="gray.600" mt={1} noOfLines={3}>
                        {insight.summary}
                      </Text>
                    </Box>
                    
                    <HStack justify="space-between" fontSize="xs" color="gray.500">
                      <Text>{insight.company_name}</Text>
                      <Text>{format(new Date(insight.created_at), 'MMM d, h:mm a')}</Text>
                    </HStack>
                    
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleViewDetail(insight)}
                      leftIcon={<FiEye />}
                    >
                      View Details
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            ))}
          </SimpleGrid>
        )}
        
        {data?.items.length === 0 && (
          <Center py={10}>
            <Text color="gray.500">No insights found matching your filters</Text>
          </Center>
        )}
      </VStack>

      <InsightDetailModal
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        insight={selectedInsight}
      />
    </DashboardLayout>
  );
}
