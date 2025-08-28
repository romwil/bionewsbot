'use client';

import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  Text,
  VStack,
  HStack,
  Badge,
  Box,
  Divider,
  useColorModeValue,
  Code,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Progress,
  List,
  ListItem,
  ListIcon,
  Icon,
  Stat,
  StatLabel,
  StatNumber,
  SimpleGrid,
} from '@chakra-ui/react';
import {
  FiCheckCircle,
  FiXCircle,
  FiClock,
  FiAlertCircle,
  FiDatabase,
  FiActivity,
  FiFileText,
} from 'react-icons/fi';
import { AnalysisRun } from '@/types';
import { format } from 'date-fns';

interface AnalysisDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  run: AnalysisRun | null;
}

export function AnalysisDetailModal({ isOpen, onClose, run }: AnalysisDetailModalProps) {
  const bgColor = useColorModeValue('gray.50', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  if (!run) return null;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return FiCheckCircle;
      case 'failed':
        return FiXCircle;
      case 'running':
        return FiClock;
      case 'pending':
        return FiAlertCircle;
      default:
        return FiAlertCircle;
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
    <Modal isOpen={isOpen} onClose={onClose} size="2xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          <HStack justify="space-between">
            <Text>Analysis Run Details</Text>
            <Badge colorScheme={getStatusColor(run.status)} size="lg">
              <HStack spacing={1}>
                <Icon as={getStatusIcon(run.status)} />
                <Text>{run.status}</Text>
              </HStack>
            </Badge>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          <Tabs colorScheme="brand">
            <TabList>
              <Tab>Overview</Tab>
              <Tab>Results</Tab>
              <Tab>Logs</Tab>
            </TabList>

            <TabPanels>
              {/* Overview Tab */}
              <TabPanel>
                <VStack align="stretch" spacing={4}>
                  <Box>
                    <Text fontWeight="bold" mb={2}>Run Information</Text>
                    <VStack align="stretch" spacing={2} pl={4}>
                      <HStack justify="space-between">
                        <Text fontSize="sm" color="gray.600">Run ID:</Text>
                        <Code fontSize="xs">{run.id}</Code>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontSize="sm" color="gray.600">Type:</Text>
                        <Badge colorScheme="purple" variant="subtle">
                          {run.analysis_type}
                        </Badge>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontSize="sm" color="gray.600">Started:</Text>
                        <Text fontSize="sm">
                          {format(new Date(run.started_at), 'PPpp')}
                        </Text>
                      </HStack>
                      {run.completed_at && (
                        <HStack justify="space-between">
                          <Text fontSize="sm" color="gray.600">Completed:</Text>
                          <Text fontSize="sm">
                            {format(new Date(run.completed_at), 'PPpp')}
                          </Text>
                        </HStack>
                      )}
                      <HStack justify="space-between">
                        <Text fontSize="sm" color="gray.600">Duration:</Text>
                        <Text fontSize="sm">
                          {run.duration ? `${run.duration} minutes` : 'In progress'}
                        </Text>
                      </HStack>
                    </VStack>
                  </Box>

                  <Divider />

                  <Box>
                    <Text fontWeight="bold" mb={2}>Progress</Text>
                    <VStack align="stretch" spacing={2}>
                      <Progress
                        value={run.progress || 0}
                        size="lg"
                        colorScheme={run.status === 'failed' ? 'red' : 'brand'}
                        hasStripe={run.status === 'running'}
                        isAnimated={run.status === 'running'}
                      />
                      <Text fontSize="sm" textAlign="center" color="gray.600">
                        {run.progress || 0}% Complete
                      </Text>
                    </VStack>
                  </Box>

                  {run.companies && run.companies.length > 0 && (
                    <>
                      <Divider />
                      <Box>
                        <Text fontWeight="bold" mb={2}>Companies Analyzed</Text>
                        <List spacing={1}>
                          {run.companies.map((company, index) => (
                            <ListItem key={index} fontSize="sm">
                              <ListIcon as={FiCheckCircle} color="green.500" />
                              {company}
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    </>
                  )}
                </VStack>
              </TabPanel>

              {/* Results Tab */}
              <TabPanel>
                <VStack align="stretch" spacing={4}>
                  {run.results ? (
                    <>
                      <SimpleGrid columns={2} spacing={4}>
                        <Stat>
                          <StatLabel>Insights Generated</StatLabel>
                          <StatNumber>{run.results.insights_count || 0}</StatNumber>
                        </Stat>
                        <Stat>
                          <StatLabel>Data Sources</StatLabel>
                          <StatNumber>{run.results.sources_count || 0}</StatNumber>
                        </Stat>
                        <Stat>
                          <StatLabel>Alerts Triggered</StatLabel>
                          <StatNumber color="orange.500">
                            {run.results.alerts_count || 0}
                          </StatNumber>
                        </Stat>
                        <Stat>
                          <StatLabel>Processing Time</StatLabel>
                          <StatNumber>{run.results.processing_time || '0'}s</StatNumber>
                        </Stat>
                      </SimpleGrid>

                      {run.results.summary && (
                        <Box>
                          <Text fontWeight="bold" mb={2}>Summary</Text>
                          <Box
                            p={4}
                            bg={bgColor}
                            borderRadius="md"
                            borderWidth="1px"
                            borderColor={borderColor}
                          >
                            <Text fontSize="sm">{run.results.summary}</Text>
                          </Box>
                        </Box>
                      )}

                      {run.results.key_findings && run.results.key_findings.length > 0 && (
                        <Box>
                          <Text fontWeight="bold" mb={2}>Key Findings</Text>
                          <List spacing={2}>
                            {run.results.key_findings.map((finding, index) => (
                              <ListItem key={index} fontSize="sm">
                                <ListIcon as={FiActivity} color="brand.500" />
                                {finding}
                              </ListItem>
                            ))}
                          </List>
                        </Box>
                      )}
                    </>
                  ) : (
                    <Box textAlign="center" py={8}>
                      <Icon as={FiFileText} boxSize={12} color="gray.400" mb={4} />
                      <Text color="gray.500">
                        {run.status === 'running' 
                          ? 'Results will appear when analysis is complete'
                          : 'No results available for this run'}
                      </Text>
                    </Box>
                  )}
                </VStack>
              </TabPanel>

              {/* Logs Tab */}
              <TabPanel>
                <Box>
                  {run.logs && run.logs.length > 0 ? (
                    <Code
                      p={4}
                      borderRadius="md"
                      fontSize="xs"
                      display="block"
                      whiteSpace="pre-wrap"
                      maxH="400px"
                      overflowY="auto"
                    >
                      {run.logs.join('\n')}
                    </Code>
                  ) : (
                    <Box textAlign="center" py={8}>
                      <Icon as={FiDatabase} boxSize={12} color="gray.400" mb={4} />
                      <Text color="gray.500">No logs available</Text>
                    </Box>
                  )}
                </Box>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </ModalBody>

        <ModalFooter>
          <Button onClick={onClose}>Close</Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
