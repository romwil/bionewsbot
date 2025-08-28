'use client';

import { Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { useColorModeValue } from '@chakra-ui/react';

ChartJS.register(ArcElement, Tooltip, Legend);

interface SentimentDistributionChartProps {
  distribution: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

export function SentimentDistributionChart({ distribution }: SentimentDistributionChartProps) {
  const textColor = useColorModeValue('gray.800', 'gray.200');
  
  const data = {
    labels: ['Positive', 'Negative', 'Neutral'],
    datasets: [
      {
        data: [distribution.positive, distribution.negative, distribution.neutral],
        backgroundColor: [
          'rgba(72, 187, 120, 0.8)', // Green for positive
          'rgba(245, 101, 101, 0.8)', // Red for negative
          'rgba(160, 174, 192, 0.8)', // Gray for neutral
        ],
        borderColor: [
          'rgba(72, 187, 120, 1)',
          'rgba(245, 101, 101, 1)',
          'rgba(160, 174, 192, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const options: ChartOptions<'doughnut'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: textColor,
          padding: 20,
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.label || '';
            const value = context.parsed || 0;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ${value} (${percentage}%)`;
          },
        },
      },
    },
  };

  return (
    <div style={{ height: '300px' }}>
      <Doughnut data={data} options={options} />
    </div>
  );
}
