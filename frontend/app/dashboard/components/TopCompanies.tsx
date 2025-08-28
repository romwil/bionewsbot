'use client';

import {
  VStack,
  HStack,
  Text,
  Badge,
  Box,
  Link,
  Avatar,
  Progress,
  useColorModeValue,
} from '@chakra-ui/react';
import { Company } from '@/types';
import NextLink from 'next/link';

interface TopCompaniesProps {
  companies: Company[];
}

export function TopCompanies({ companies }: TopCompaniesProps) {
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const progressBg = useColorModeValue('gray.200', 'gray.600');

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

  if (companies.length === 0) {
    return (
      <Box py={8} textAlign="center">
        <Text color="gray.500">No companies available</Text>
      </Box>
    );
  }

  // Calculate max insights for progress bar scaling
  const maxInsights = Math.max(...companies.map(c => c.insights_count || 0));

  return (
    <VStack spacing={3} align="stretch">
      {companies.map((company) => (
        <Box
          key={company.id}
          p={4}
          borderWidth="1px"
          borderColor={borderColor}
          borderRadius="md"
          _hover={{ bg: hoverBg, cursor: 'pointer' }}
          transition="all 0.2s"
        >
          <Link as={NextLink} href={`/companies/${company.id}`} _hover={{ textDecoration: 'none' }}>
            <VStack align="stretch" spacing={3}>
              <HStack justify="space-between">
                <HStack spacing={3}>
                  <Avatar 
                    size="sm" 
                    name={company.name} 
                    bg="brand.500"
                  />
                  <Box>
                    <Text fontWeight="medium">{company.name}</Text>
                    {company.ticker && (
                      <Text fontSize="xs" color="gray.500">
                        {company.ticker}
                      </Text>
                    )}
                  </Box>
                </HStack>
                <Badge colorScheme={getStatusColor(company.monitoring_status)} size="sm">
                  {company.monitoring_status}
                </Badge>
              </HStack>
              
              <HStack justify="space-between" fontSize="sm">
                <Text color="gray.600">{company.industry}</Text>
                <Text fontWeight="medium">
                  {company.insights_count || 0} insights
                </Text>
              </HStack>
              
              {maxInsights > 0 && (
                <Progress 
                  value={(company.insights_count || 0) / maxInsights * 100} 
                  size="xs" 
                  colorScheme="brand"
                  bg={progressBg}
                  borderRadius="full"
                />
              )}
            </VStack>
          </Link>
        </Box>
      ))}
    </VStack>
  );
}
