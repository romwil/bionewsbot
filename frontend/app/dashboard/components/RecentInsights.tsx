'use client';

import {
  VStack,
  HStack,
  Text,
  Badge,
  Box,
  Link,
  Icon,
  useColorModeValue,
} from '@chakra-ui/react';
import { FiExternalLink, FiClock } from 'react-icons/fi';
import { format } from 'date-fns';
import { Insight } from '@/types';
import NextLink from 'next/link';

interface RecentInsightsProps {
  insights: Insight[];
}

export function RecentInsights({ insights }: RecentInsightsProps) {
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

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

  if (insights.length === 0) {
    return (
      <Box py={8} textAlign="center">
        <Text color="gray.500">No recent insights available</Text>
      </Box>
    );
  }

  return (
    <VStack spacing={3} align="stretch">
      {insights.map((insight) => (
        <Box
          key={insight.id}
          p={4}
          borderWidth="1px"
          borderColor={borderColor}
          borderRadius="md"
          _hover={{ bg: hoverBg, cursor: 'pointer' }}
          transition="all 0.2s"
        >
          <Link as={NextLink} href={`/insights/${insight.id}`} _hover={{ textDecoration: 'none' }}>
            <VStack align="stretch" spacing={2}>
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
                <Icon as={FiExternalLink} color="gray.400" />
              </HStack>
              
              <Text fontWeight="medium" noOfLines={2}>
                {insight.title}
              </Text>
              
              <Text fontSize="sm" color="gray.600" noOfLines={2}>
                {insight.summary}
              </Text>
              
              <HStack justify="space-between" fontSize="xs" color="gray.500">
                <Text>{insight.company_name}</Text>
                <HStack spacing={1}>
                  <Icon as={FiClock} />
                  <Text>{format(new Date(insight.created_at), 'MMM d, h:mm a')}</Text>
                </HStack>
              </HStack>
            </VStack>
          </Link>
        </Box>
      ))}
    </VStack>
  );
}
