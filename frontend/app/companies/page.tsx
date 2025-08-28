'use client';

import {
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
  Heading,
  HStack,
  IconButton,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Badge,
  Text,
  useDisclosure,
  useToast,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Spinner,
  Center,
  VStack,
  Avatar,
  Flex,
  useColorModeValue,
} from '@chakra-ui/react';
import {
  FiPlus,
  FiSearch,
  FiEdit,
  FiTrash2,
  FiMoreVertical,
  FiRefreshCw,
  FiDownload,
} from 'react-icons/fi';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { CompanyModal } from './components/CompanyModal';
import { DeleteConfirmDialog } from '@/components/common/DeleteConfirmDialog';
import { companiesApi } from '@/lib/api/companies';
import { Company } from '@/types';
import { format } from 'date-fns';

export default function CompaniesPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const cardBg = useColorModeValue('white', 'gray.800');
  
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [companyToDelete, setCompanyToDelete] = useState<Company | null>(null);
  
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();

  // Fetch companies
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['companies', searchTerm, statusFilter],
    queryFn: () => companiesApi.getCompanies({
      search: searchTerm,
      status: statusFilter !== 'all' ? statusFilter : undefined,
    }),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => companiesApi.deleteCompany(id),
    onSuccess: () => {
      toast({
        title: 'Company deleted',
        description: 'The company has been successfully deleted.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      onDeleteClose();
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to delete company. Please try again.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    },
  });

  const handleEdit = (company: Company) => {
    setSelectedCompany(company);
    onOpen();
  };

  const handleDelete = (company: Company) => {
    setCompanyToDelete(company);
    onDeleteOpen();
  };

  const handleAddNew = () => {
    setSelectedCompany(null);
    onOpen();
  };

  const handleModalClose = () => {
    setSelectedCompany(null);
    onClose();
  };

  const confirmDelete = () => {
    if (companyToDelete) {
      deleteMutation.mutate(companyToDelete.id);
    }
  };

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

  const exportCompanies = () => {
    // TODO: Implement CSV export
    toast({
      title: 'Export started',
      description: 'Your companies list is being exported.',
      status: 'info',
      duration: 3000,
      isClosable: true,
    });
  };

  return (
    <DashboardLayout>
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>Companies</Heading>
          <Text color="gray.600">Manage and monitor life sciences companies</Text>
        </Box>

        <Card bg={cardBg}>
          <CardHeader>
            <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
              <HStack spacing={4} flex={1}>
                <InputGroup maxW="md">
                  <InputLeftElement pointerEvents="none">
                    <FiSearch color="gray.300" />
                  </InputLeftElement>
                  <Input
                    placeholder="Search companies..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </InputGroup>
                
                <Select
                  maxW="200px"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="paused">Paused</option>
                  <option value="archived">Archived</option>
                </Select>
              </HStack>
              
              <HStack>
                <IconButton
                  aria-label="Refresh"
                  icon={<FiRefreshCw />}
                  variant="ghost"
                  onClick={() => refetch()}
                />
                <IconButton
                  aria-label="Export"
                  icon={<FiDownload />}
                  variant="ghost"
                  onClick={exportCompanies}
                />
                <Button
                  leftIcon={<FiPlus />}
                  colorScheme="brand"
                  onClick={handleAddNew}
                >
                  Add Company
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
                      <Th>Company</Th>
                      <Th>Industry</Th>
                      <Th>Status</Th>
                      <Th isNumeric>Insights</Th>
                      <Th>Last Updated</Th>
                      <Th width="50px"></Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {data?.items.map((company) => (
                      <Tr key={company.id} _hover={{ bg: useColorModeValue('gray.50', 'gray.700') }}>
                        <Td>
                          <HStack spacing={3}>
                            <Avatar size="sm" name={company.name} bg="brand.500" />
                            <Box>
                              <Text fontWeight="medium">{company.name}</Text>
                              {company.ticker && (
                                <Text fontSize="sm" color="gray.500">
                                  {company.ticker}
                                </Text>
                              )}
                            </Box>
                          </HStack>
                        </Td>
                        <Td>{company.industry}</Td>
                        <Td>
                          <Badge colorScheme={getStatusColor(company.monitoring_status)}>
                            {company.monitoring_status}
                          </Badge>
                        </Td>
                        <Td isNumeric>{company.insights_count || 0}</Td>
                        <Td>
                          <Text fontSize="sm">
                            {format(new Date(company.updated_at), 'MMM d, yyyy')}
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
                              <MenuItem icon={<FiEdit />} onClick={() => handleEdit(company)}>
                                Edit
                              </MenuItem>
                              <MenuItem
                                icon={<FiTrash2 />}
                                onClick={() => handleDelete(company)}
                                color="red.500"
                              >
                                Delete
                              </MenuItem>
                            </MenuList>
                          </Menu>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
                
                {data?.items.length === 0 && (
                  <Center py={10}>
                    <Text color="gray.500">No companies found</Text>
                  </Center>
                )}
              </TableContainer>
            )}
          </CardBody>
        </Card>
      </VStack>

      <CompanyModal
        isOpen={isOpen}
        onClose={handleModalClose}
        company={selectedCompany}
      />

      <DeleteConfirmDialog
        isOpen={isDeleteOpen}
        onClose={onDeleteClose}
        onConfirm={confirmDelete}
        title="Delete Company"
        message={`Are you sure you want to delete ${companyToDelete?.name}? This action cannot be undone.`}
        isLoading={deleteMutation.isPending}
      />
    </DashboardLayout>
  );
}
