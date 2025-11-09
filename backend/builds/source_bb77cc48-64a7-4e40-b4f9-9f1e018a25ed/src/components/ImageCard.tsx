
import React from 'react';
import { Download } from 'lucide-react';
import { Button } from './ui/button';
import {
  Card,
  CardContent,
  CardFooter,
} from './ui/card';

interface ImageCardProps {
  image: {
    id: string;
    title: string;
    url: string;
    preview: string;
  };
}

const ImageCard = ({ image }: ImageCardProps) => {
  return (
    <Card className="group overflow-hidden backdrop-blur-sm bg-white/80 border hover:shadow-lg transition-all duration-300">
      <CardContent className="p-0 relative overflow-hidden">
        <img
          src={image.preview}
          alt={image.title}
          className="w-full aspect-square object-cover transition-transform duration-300 group-hover:scale-105"
          loading="lazy"
        />
      </CardContent>
      <CardFooter className="p-4 flex justify-between items-center">
        <p className="text-sm truncate flex-1">{image.title}</p>
        <Button
          variant="ghost"
          size="icon"
          className="ml-2 hover:scale-110 transition-transform duration-300"
          onClick={() => window.open(image.url, '_blank')}
        >
          <Download className="w-4 h-4" />
        </Button>
      </CardFooter>
    </Card>
  );
};

export default ImageCard;
