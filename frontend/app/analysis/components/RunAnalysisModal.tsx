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
  FormControl,
  FormLabel,
  FormErrorMessage,
  FormHelperText,
  Select,
  VStack,
  useToast,
  Checkbox,
  CheckboxGroup,
  Stack,
  Text,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { useForm, Controller } from 'react-hook-form';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { analysisApi } from '@/lib/api/analysis';
import { companiesApi } from '@/lib/api/companies';
import { useState } from 'react';

interface RunAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface AnalysisFormData {
  analysis_type: string;
  company_ids: string[];
}

export function RunAnalysisModal({ isOpen, onClose }: RunAnalysisModalProps) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AnalysisFormData>({
    defaultValues: {
      analysis_type: 'comprehensive',
      company_ids: [],
    },
  });

  // Fetch companies for selection
  const { data: companies } = useQuery({
    queryKey: ['companies-for-analysis'],
    queryFn: () => companiesApi.getCompanies({ status: 'active' }),
  });

  const runAnalysisMutation = useMutation({
    mutationFn: (data: AnalysisFormData) => analysisApi.runAnalysis(data),
    onSuccess: () => {
      toast({
        title: 'Analysis started',
        description: 'Your analysis run has been queued and will start processing shortly.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      queryClient.invalidateQueries({ queryKey: ['analysis-runs'] });
      queryClient.invalidateQueries({ queryKey: ['analysis-stats'] });
      reset();
      onClose();
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to start analysis.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    },
  });

  const onSubmit = (data: AnalysisFormData) => {
    if (selectedCompanies.length === 0) {
      toast({
        title: 'No companies selected',
        description: 'Please select at least one company to analyze.',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    runAnalysisMutation.mutate({
      ...data,
      company_ids: selectedCompanies,
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <ModalHeader>Run New Analysis</ModalHeader>
          <ModalCloseButton />
          
          <ModalBody>
            <VStack spacing={6}>
              <Alert status="info" borderRadius="md">
                <AlertIcon />
                <Text fontSize="sm">
                  Analysis runs collect and process the latest data for selected companies.
                  This may take several minutes depending on the analysis type and number of companies.
                </Text>
              </Alert>

              <FormControl isInvalid={!!errors.analysis_type} isRequired>
                <FormLabel>Analysis Type</FormLabel>
                <Select
                  {...register('analysis_type', {
                    required: 'Analysis type is required',
                  })}
                >
                  <option value="comprehensive">Comprehensive Analysis</option>
                  <option value="news_sentiment">News & Sentiment Analysis</option>
                  <option value="financial">Financial Analysis</option>
                  <option value="regulatory">Regulatory Compliance Check</option>
                  <option value="competitive">Competitive Intelligence</option>
                  <option value="quick_scan">Quick Scan</option>
                </Select>
                <FormHelperText>
                  Choose the type of analysis to run on selected companies
                </FormHelperText>
                <FormErrorMessage>{errors.analysis_type?.message}</FormErrorMessage>
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Select Companies</FormLabel>
                <Text fontSize="sm" color="gray.600" mb={3}>
                  Choose which companies to include in this analysis run
                </Text>
                
                <CheckboxGroup
                  value={selectedCompanies}
                  onChange={(values) => setSelectedCompanies(values as string[])}
                >
                  <Stack maxH="300px" overflowY="auto" spacing={2} p={3} borderWidth="1px" borderRadius="md">
                    {companies?.items.map((company) => (
                      <Checkbox key={company.id} value={company.id}>
                        <VStack align="start" spacing={0}>
                          <Text fontWeight="medium">{company.name}</Text>
                          <Text fontSize="xs" color="gray.500">
                            {company.industry} • {company.ticker || 'No ticker'}
                          </Text>
                        </VStack>
                      </Checkbox>
                    ))}
                  </Stack>
                </CheckboxGroup>
                
                {companies?.items.length === 0 && (
                  <Alert status="warning" mt={2}>
                    <AlertIcon />
                    <Text fontSize="sm">
                      No active companies found. Please add and activate companies first.
                    </Text>
                  </Alert>
                )}
              </FormControl>

              <Alert status="warning" borderRadius="md">
                <AlertIcon />
                <Text fontSize="sm">
                  <strong>Note:</strong> Running analysis will consume API credits based on the
                  number of companies and data sources accessed.
                </Text>
              </Alert>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              colorScheme="brand"
              isLoading={isSubmitting || runAnalysisMutation.isPending}
              loadingText="Starting analysis..."
              isDisabled={selectedCompanies.length === 0}
            >
              Start Analysis
            </Button>
          </ModalFooter>
        </form>
      </ModalContent>
    </Modal>
  );
}
