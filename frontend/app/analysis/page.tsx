'use client';

import {
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
  Heading,
  HStack,
  VStack,
  Text,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Badge,
  IconButton,
  useToast,
  useDisclosure,
  Spinner,
  Center,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
  useColorModeValue,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Flex,
} from '@chakra-ui/react';
import {
  FiPlay,
  FiRefreshCw,
  FiMoreVertical,
  FiEye,
  FiTrash2,
  FiClock,
  FiCheckCircle,
  FiXCircle,
  FiAlertCircle,
} from 'react-icons/fi';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { RunAnalysisModal } from './components/RunAnalysisModal';
import { AnalysisDetailModal } from './components/AnalysisDetailModal';
import { analysisApi } from '@/lib/api/analysis';
import { AnalysisRun } from '@/types';
import { format, formatDistanceToNow } from 'date-fns';

export default function AnalysisPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const cardBg = useColorModeValue('white', 'gray.800');
  
  const [selectedRun, setSelectedRun] = useState<AnalysisRun | null>(null);
  const { isOpen: isRunOpen, onOpen: onRunOpen, onClose: onRunClose } = useDisclosure();
  const { isOpen: isDetailOpen, onOpen: onDetailOpen, onClose: onDetailClose } = useDisclosure();

  // Fetch analysis runs
  const { data: runs, isLoading, refetch } = useQuery({
    queryKey: ['analysis-runs'],
    queryFn: () => analysisApi.getAnalysisRuns(),
    refetchInterval: 5000, // Refresh every 5 seconds to update status
  });

  // Fetch analysis stats
  const { data: stats } = useQuery({
    queryKey: ['analysis-stats'],
    queryFn: () => analysisApi.getAnalysisStats(),
  });

  // Cancel analysis mutation
  const cancelMutation = useMutation({
    mutationFn: (id: string) => analysisApi.cancelAnalysis(id),
    onSuccess: () => {
      toast({
        title: 'Analysis cancelled',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      queryClient.invalidateQueries({ queryKey: ['analysis-runs'] });
    },
  });

  const handleViewDetails = (run: AnalysisRun) => {
    setSelectedRun(run);
    onDetailOpen();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <FiCheckCircle color="green" />;
      case 'failed':
        return <FiXCircle color="red" />;
      case 'running':
        return <FiClock color="orange" />;
      case 'pending':
        return <FiAlertCircle color="gray" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'green';
      case 'failed':
        return 'red';
      case 'running':
        return 'orange';
      case 'pending':
        return 'gray';
      default:
        return 'gray';
    }
  };

  return (
    <DashboardLayout>
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>Analysis</Heading>
          <Text color="gray.600">Monitor and manage analysis runs</Text>
        </Box>

        {/* Stats Cards */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Total Runs</StatLabel>
                <StatNumber>{stats?.total_runs || 0}</StatNumber>
                <StatHelpText>
                  All time analysis runs
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Success Rate</StatLabel>
                <StatNumber>{stats?.success_rate || 0}%</StatNumber>
                <StatHelpText>
                  Completed successfully
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Active Runs</StatLabel>
                <StatNumber>{stats?.active_runs || 0}</StatNumber>
                <StatHelpText>
                  Currently processing
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Avg Duration</StatLabel>
                <StatNumber>{stats?.avg_duration || '0'}m</StatNumber>
                <StatHelpText>
                  Average run time
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Analysis Runs Table */}
        <Card bg={cardBg}>
          <CardHeader>
            <Flex justify="space-between" align="center">
              <Heading size="md">Analysis History</Heading>
              <HStack>
                <IconButton
                  aria-label="Refresh"
                  icon={<FiRefreshCw />}
                  variant="ghost"
                  onClick={() => refetch()}
                />
                <Button
                  leftIcon={<FiPlay />}
                  colorScheme="brand"
                  onClick={onRunOpen}
                >
                  Run Analysis
                </Button>
              </HStack>
            </Flex>
          </CardHeader>
          
          <CardBody>
            {isLoading ? (
              <Center py={10}>
                <Spinner size="xl" color="brand.500" />
              </Center>
            ) : (
              <TableContainer>
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Run ID</Th>
                      <Th>Type</Th>
                      <Th>Status</Th>
                      <Th>Progress</Th>
                      <Th>Started</Th>
                      <Th>Duration</Th>
                      <Th width="50px"></Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {runs?.items.map((run) => (
                      <Tr key={run.id}>
                        <Td>
                          <HStack>
                            {getStatusIcon(run.status)}
                            <Text fontSize="sm" fontFamily="mono">
                              {run.id.slice(0, 8)}
                            </Text>
                          </HStack>
                        </Td>
                        <Td>
                          <Badge colorScheme="purple" variant="subtle">
                            {run.analysis_type}
                          </Badge>
                        </Td>
                        <Td>
                          <Badge colorScheme={getStatusColor(run.status)}>
                            {run.status}
                          </Badge>
                        </Td>
                        <Td>
                          {run.status === 'running' ? (
                            <Progress
                              value={run.progress || 0}
                              size="sm"
                              colorScheme="brand"
                              hasStripe
                              isAnimated
                            />
                          ) : (
                            <Text fontSize="sm" color="gray.500">
                              {run.progress || 0}%
                            </Text>
                          )}
                        </Td>
                        <Td>
                          <VStack align="start" spacing={0}>
                            <Text fontSize="sm">
                              {format(new Date(run.started_at), 'MMM d, yyyy')}
                            </Text>
                            <Text fontSize="xs" color="gray.500">
                              {formatDistanceToNow(new Date(run.started_at), { addSuffix: true })}
                            </Text>
                          </VStack>
                        </Td>
                        <Td>
                          <Text fontSize="sm">
                            {run.duration ? `${run.duration}m` : '-'}
                          </Text>
                        </Td>
                        <Td>
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
                                onClick={() => handleViewDetails(run)}
                              >
                                View Details
                              </MenuItem>
                              {run.status === 'running' && (
                                <MenuItem
                                  icon={<FiXCircle />}
                                  onClick={() => cancelMutation.mutate(run.id)}
                                  color="red.500"
                                >
                                  Cancel Run
                                </MenuItem>
                              )}
                            </MenuList>
                          </Menu>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
                
                {runs?.items.length === 0 && (
                  <Center py={10}>
                    <VStack>
                      <Text color="gray.500">No analysis runs yet</Text>
                      <Button
                        size="sm"
                        colorScheme="brand"
                        variant="outline"
                        onClick={onRunOpen}
                      >
                        Run Your First Analysis
                      </Button>
                    </VStack>
                  </Center>
                )}
              </TableContainer>
            )}
          </CardBody>
        </Card>
      </VStack>

      <RunAnalysisModal
        isOpen={isRunOpen}
        onClose={onRunClose}
      />

      <AnalysisDetailModal
        isOpen={isDetailOpen}
        onClose={onDetailClose}
        run={selectedRun}
      />
    </DashboardLayout>
  );
}
