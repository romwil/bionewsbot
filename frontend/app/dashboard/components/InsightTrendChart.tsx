'use client';

import { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { useColorModeValue } from '@chakra-ui/react';
import { useQuery } from '@tanstack/react-query';
import { format, subDays } from 'date-fns';
import apiClient from '@/lib/api/client';
import { TrendData } from '@/types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const fetchInsightTrends = async (): Promise<TrendData[]> => {
  const response = await apiClient.get('/insights/trends', {
    params: {
      days: 7,
    },
  });
  return response.data;
};

export function InsightTrendChart() {
  const gridColor = useColorModeValue('rgba(0, 0, 0, 0.1)', 'rgba(255, 255, 255, 0.1)');
  const textColor = useColorModeValue('gray.800', 'gray.200');
  
  const { data: trends, isLoading } = useQuery({
    queryKey: ['insight-trends'],
    queryFn: fetchInsightTrends,
  });

  const chartData = {
    labels: trends?.map(t => format(new Date(t.date), 'MMM d')) || [],
    datasets: [
      {
        label: 'Insights',
        data: trends?.map(t => t.value) || [],
        borderColor: 'rgb(0, 128, 255)',
        backgroundColor: 'rgba(0, 128, 255, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        mode: 'index',
        intersect: false,
      },
    },
    scales: {
      x: {
        grid: {
          color: gridColor,
        },
        ticks: {
          color: textColor,
        },
      },
      y: {
        grid: {
          color: gridColor,
        },
        ticks: {
          color: textColor,
          precision: 0,
        },
      },
    },
  };

  if (isLoading) {
    return <div style={{ height: '300px' }}>Loading...</div>;
  }

  return (
    <div style={{ height: '300px' }}>
      <Line data={chartData} options={options} />
    </div>
  );
}
