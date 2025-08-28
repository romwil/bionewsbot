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
  Input,
  Select,
  Textarea,
  VStack,
  HStack,
  useToast,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Company, CompanyCreate, CompanyUpdate } from '@/types';
import { companiesApi } from '@/lib/api/companies';
import { useEffect } from 'react';

interface CompanyModalProps {
  isOpen: boolean;
  onClose: () => void;
  company?: Company | null;
}

export function CompanyModal({ isOpen, onClose, company }: CompanyModalProps) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const isEditMode = !!company;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CompanyCreate>();

  useEffect(() => {
    if (company) {
      reset({
        name: company.name,
        ticker: company.ticker || '',
        industry: company.industry,
        description: company.description || '',
        website: company.website || '',
        monitoring_status: company.monitoring_status,
      });
    } else {
      reset({
        name: '',
        ticker: '',
        industry: '',
        description: '',
        website: '',
        monitoring_status: 'active',
      });
    }
  }, [company, reset]);

  const createMutation = useMutation({
    mutationFn: (data: CompanyCreate) => companiesApi.createCompany(data),
    onSuccess: () => {
      toast({
        title: 'Company created',
        description: 'The company has been successfully created.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      onClose();
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create company.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: CompanyUpdate }) => 
      companiesApi.updateCompany(id, data),
    onSuccess: () => {
      toast({
        title: 'Company updated',
        description: 'The company has been successfully updated.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      onClose();
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update company.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    },
  });

  const onSubmit = (data: CompanyCreate) => {
    if (isEditMode && company) {
      updateMutation.mutate({ id: company.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <ModalHeader>
            {isEditMode ? 'Edit Company' : 'Add New Company'}
          </ModalHeader>
          <ModalCloseButton />
          
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isInvalid={!!errors.name} isRequired>
                <FormLabel>Company Name</FormLabel>
                <Input
                  placeholder="Enter company name"
                  {...register('name', {
                    required: 'Company name is required',
                    minLength: {
                      value: 2,
                      message: 'Company name must be at least 2 characters',
                    },
                  })}
                />
                <FormErrorMessage>{errors.name?.message}</FormErrorMessage>
              </FormControl>

              <HStack spacing={4} width="full">
                <FormControl isInvalid={!!errors.ticker}>
                  <FormLabel>Ticker Symbol</FormLabel>
                  <Input
                    placeholder="e.g., AAPL"
                    textTransform="uppercase"
                    {...register('ticker', {
                      pattern: {
                        value: /^[A-Z]{1,5}$/,
                        message: 'Invalid ticker format',
                      },
                    })}
                  />
                  <FormErrorMessage>{errors.ticker?.message}</FormErrorMessage>
                </FormControl>

                <FormControl isInvalid={!!errors.industry} isRequired>
                  <FormLabel>Industry</FormLabel>
                  <Select
                    placeholder="Select industry"
                    {...register('industry', {
                      required: 'Industry is required',
                    })}
                  >
                    <option value="Pharmaceuticals">Pharmaceuticals</option>
                    <option value="Biotechnology">Biotechnology</option>
                    <option value="Medical Devices">Medical Devices</option>
                    <option value="Healthcare Services">Healthcare Services</option>
                    <option value="Life Sciences Tools">Life Sciences Tools</option>
                    <option value="Diagnostics">Diagnostics</option>
                    <option value="Other">Other</option>
                  </Select>
                  <FormErrorMessage>{errors.industry?.message}</FormErrorMessage>
                </FormControl>
              </HStack>

              <FormControl isInvalid={!!errors.website}>
                <FormLabel>Website</FormLabel>
                <Input
                  placeholder="https://example.com"
                  {...register('website', {
                    pattern: {
                      value: /^https?:\/\/.+/,
                      message: 'Please enter a valid URL',
                    },
                  })}
                />
                <FormErrorMessage>{errors.website?.message}</FormErrorMessage>
              </FormControl>

              <FormControl isInvalid={!!errors.description}>
                <FormLabel>Description</FormLabel>
                <Textarea
                  placeholder="Brief description of the company"
                  rows={3}
                  {...register('description', {
                    maxLength: {
                      value: 500,
                      message: 'Description must be less than 500 characters',
                    },
                  })}
                />
                <FormErrorMessage>{errors.description?.message}</FormErrorMessage>
              </FormControl>

              <FormControl isInvalid={!!errors.monitoring_status} isRequired>
                <FormLabel>Monitoring Status</FormLabel>
                <Select
                  {...register('monitoring_status', {
                    required: 'Monitoring status is required',
                  })}
                >
                  <option value="active">Active</option>
                  <option value="paused">Paused</option>
                  <option value="archived">Archived</option>
                </Select>
                <FormErrorMessage>{errors.monitoring_status?.message}</FormErrorMessage>
              </FormControl>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              colorScheme="brand"
              isLoading={isSubmitting || createMutation.isPending || updateMutation.isPending}
              loadingText={isEditMode ? 'Updating...' : 'Creating...'}
            >
              {isEditMode ? 'Update' : 'Create'}
            </Button>
          </ModalFooter>
        </form>
      </ModalContent>
    </Modal>
  );
}
