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
  Link,
  Divider,
  useColorModeValue,
  IconButton,
  useToast,
  Heading,
  Code,
} from '@chakra-ui/react';
import {
  FiExternalLink,
  FiFlag,
  FiClock,
  FiUser,
  FiTag,
  FiTrendingUp,
} from 'react-icons/fi';
import { Insight } from '@/types';
import { format } from 'date-fns';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { insightsApi } from '@/lib/api/insights';

interface InsightDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  insight: Insight | null;
}

export function InsightDetailModal({ isOpen, onClose, insight }: InsightDetailModalProps) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const bgColor = useColorModeValue('gray.50', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

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

  if (!insight) return null;

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
    <Modal isOpen={isOpen} onClose={onClose} size="2xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          <HStack justify="space-between">
            <Text>Insight Details</Text>
            <HStack>
              <IconButton
                aria-label="Toggle flag"
                icon={<FiFlag />}
                size="sm"
                variant={insight.is_flagged ? 'solid' : 'outline'}
                colorScheme={insight.is_flagged ? 'red' : 'gray'}
                onClick={() => toggleFlagMutation.mutate({
                  id: insight.id,
                  flagged: !insight.is_flagged,
                })}
              />
            </HStack>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          <VStack align="stretch" spacing={4}>
            {/* Title and Badges */}
            <Box>
              <Heading size="md" mb={2}>
                {insight.title}
              </Heading>
              <HStack spacing={2} wrap="wrap">
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
            </Box>

            <Divider />

            {/* Summary */}
            <Box>
              <Text fontWeight="bold" mb={2}>Summary</Text>
              <Text>{insight.summary}</Text>
            </Box>

            {/* Full Content */}
            {insight.content && (
              <Box>
                <Text fontWeight="bold" mb={2}>Full Content</Text>
                <Box
                  p={4}
                  bg={bgColor}
                  borderRadius="md"
                  borderWidth="1px"
                  borderColor={borderColor}
                  maxH="300px"
                  overflowY="auto"
                >
                  <Text whiteSpace="pre-wrap">{insight.content}</Text>
                </Box>
              </Box>
            )}

            {/* Metadata */}
            <Box>
              <Text fontWeight="bold" mb={2}>Details</Text>
              <VStack align="stretch" spacing={2}>
                <HStack>
                  <Icon as={FiUser} color="gray.500" />
                  <Text fontSize="sm">
                    <strong>Company:</strong> {insight.company_name}
                  </Text>
                </HStack>
                <HStack>
                  <Icon as={FiClock} color="gray.500" />
                  <Text fontSize="sm">
                    <strong>Created:</strong> {format(new Date(insight.created_at), 'PPpp')}
                  </Text>
                </HStack>
                <HStack>
                  <Icon as={FiTrendingUp} color="gray.500" />
                  <Text fontSize="sm">
                    <strong>Confidence:</strong> {Math.round(insight.confidence_score * 100)}%
                  </Text>
                </HStack>
                {insight.keywords && insight.keywords.length > 0 && (
                  <HStack align="start">
                    <Icon as={FiTag} color="gray.500" mt={1} />
                    <Box>
                      <Text fontSize="sm" fontWeight="bold">Keywords:</Text>
                      <HStack spacing={2} wrap="wrap" mt={1}>
                        {insight.keywords.map((keyword, index) => (
                          <Badge key={index} size="sm" variant="subtle">
                            {keyword}
                          </Badge>
                        ))}
                      </HStack>
                    </Box>
                  </HStack>
                )}
              </VStack>
            </Box>

            {/* Source */}
            <Box>
              <Text fontWeight="bold" mb={2}>Source</Text>
              <Link
                href={insight.source_url}
                isExternal
                color="brand.500"
                display="flex"
                alignItems="center"
                gap={2}
              >
                <Icon as={FiExternalLink} />
                <Text fontSize="sm" noOfLines={1}>
                  {insight.source_url}
                </Text>
              </Link>
            </Box>

            {/* Raw Data (if available) */}
            {insight.raw_data && (
              <Box>
                <Text fontWeight="bold" mb={2}>Raw Data</Text>
                <Code
                  p={4}
                  borderRadius="md"
                  fontSize="xs"
                  maxH="200px"
                  overflowY="auto"
                  display="block"
                  whiteSpace="pre"
                >
                  {JSON.stringify(insight.raw_data, null, 2)}
                </Code>
              </Box>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Close
          </Button>
          <Button
            as="a"
            href={insight.source_url}
            target="_blank"
            rel="noopener noreferrer"
            colorScheme="brand"
            leftIcon={<FiExternalLink />}
          >
            View Source
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
