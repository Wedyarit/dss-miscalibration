'use client';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

interface DataTableProps {
  data: Array<{
    item_id: number;
    stem: string;
    tags: string[];
    confident_error_rate: number;
    total_interactions: number;
    avg_confidence: number;
    avg_accuracy: number;
  }>;
  title: string;
  headers?: {
    question: string;
    tags: string;
    confidentErrorRate: string;
    interactions: string;
    avgConfidence: string;
    avgAccuracy: string;
  };
}

export function DataTable({ data, title, headers }: DataTableProps) {
  const defaultHeaders = {
    question: 'Question',
    tags: 'Tags',
    confidentErrorRate: 'Confident Error Rate',
    interactions: 'Interactions',
    avgConfidence: 'Avg Confidence',
    avgAccuracy: 'Avg Accuracy',
  };

  const tableHeaders = headers || defaultHeaders;
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2 font-medium">{tableHeaders.question}</th>
                <th className="text-left p-2 font-medium">{tableHeaders.tags}</th>
                <th className="text-left p-2 font-medium">{tableHeaders.confidentErrorRate}</th>
                <th className="text-left p-2 font-medium">{tableHeaders.interactions}</th>
                <th className="text-left p-2 font-medium">{tableHeaders.avgConfidence}</th>
                <th className="text-left p-2 font-medium">{tableHeaders.avgAccuracy}</th>
              </tr>
            </thead>
            <tbody>
              {data.map((item) => (
                <tr key={item.item_id} className="border-b hover:bg-muted/50">
                  <td className="p-2">
                    <div className="max-w-xs truncate" title={item.stem}>
                      {item.stem}
                    </div>
                  </td>
                  <td className="p-2">
                    <div className="flex flex-wrap gap-1">
                      {item.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </td>
                  <td className="p-2">
                    <Badge variant={item.confident_error_rate > 0.3 ? 'destructive' : 'secondary'}>
                      {(item.confident_error_rate * 100).toFixed(1)}%
                    </Badge>
                  </td>
                  <td className="p-2">{item.total_interactions}</td>
                  <td className="p-2">{(item.avg_confidence * 100).toFixed(1)}%</td>
                  <td className="p-2">{(item.avg_accuracy * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
