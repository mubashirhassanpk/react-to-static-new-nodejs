
import { Download, ImageIcon } from 'lucide-react';
import { Button } from '../ui/button';
import { ImageState } from './types';

interface ProcessedImageProps {
  imageState: ImageState;
  onDownload: () => void;
}

export const ProcessedImage = ({ imageState, onDownload }: ProcessedImageProps) => {
  const { processedImage } = imageState;

  return (
    <div className="space-y-6">
      <div className="h-[300px] sm:h-[400px] border-2 border-dashed border-gray-300 rounded-xl overflow-hidden bg-gradient-to-br from-gray-50 to-white backdrop-blur-xl shadow-lg group">
        {processedImage ? (
          <img
            src={processedImage}
            alt="Processed"
            className="w-full h-full object-contain animate-scale-in"
          />
        ) : (
          <div className="flex flex-col items-center justify-center w-full h-full text-gray-500 p-4">
            <div className="relative w-16 h-16 mb-4">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-blue-500 rounded-full animate-pulse"></div>
              <ImageIcon className="w-full h-full text-white relative z-10" />
            </div>
            <p className="text-center">Your image with removed background will appear here</p>
            <p className="text-sm text-gray-400 mt-2">Ultra HD Quality Guaranteed!</p>
          </div>
        )}
      </div>
      {processedImage && (
        <Button 
          onClick={onDownload} 
          className="w-full bg-gradient-to-r from-green-500 to-emerald-600 transition-all duration-300 hover:scale-105 animate-fade-in"
        >
          <Download className="mr-2 h-4 w-4" />
          Download Ultra HD Image
        </Button>
      )}
    </div>
  );
};
