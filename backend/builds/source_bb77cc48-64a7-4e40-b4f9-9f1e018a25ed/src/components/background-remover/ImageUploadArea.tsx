
import { Upload, Trash2, Sparkles } from 'lucide-react';
import { Button } from '../ui/button';
import { toast } from '../ui/use-toast';
import { SAMPLE_IMAGES } from './constants';
import { ImageState } from './types';

interface ImageUploadAreaProps {
  imageState: ImageState;
  onImageUpload: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
  onSampleImageClick: (url: string) => Promise<void>;
  onReset: () => void;
  onRemoveBackground: () => Promise<void>;
}

export const ImageUploadArea = ({
  imageState,
  onImageUpload,
  onSampleImageClick,
  onReset,
  onRemoveBackground
}: ImageUploadAreaProps) => {
  const { originalImage, isProcessing } = imageState;

  return (
    <div className="space-y-6">
      <div className="relative h-[300px] sm:h-[400px] border-2 border-dashed border-gray-300 rounded-xl overflow-hidden bg-gradient-to-br from-gray-50 to-white backdrop-blur-xl shadow-lg transition-all duration-300 hover:shadow-xl group">
        {!originalImage ? (
          <label className="flex flex-col items-center justify-center w-full h-full cursor-pointer transition-transform duration-300 hover:scale-105">
            <div className="relative">
              <Upload className="w-16 h-16 text-gray-400 animate-bounce" />
              <div className="absolute top-0 right-0 -mr-2 -mt-2">
                <div className="bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                  FREE
                </div>
              </div>
            </div>
            <span className="mt-4 text-gray-500 text-lg font-medium">Drop your image here</span>
            <span className="text-sm text-gray-400 mt-2">or click to upload</span>
            <input
              type="file"
              className="hidden"
              accept="image/*"
              onChange={onImageUpload}
            />
          </label>
        ) : (
          <img
            src={originalImage}
            alt="Original"
            className="w-full h-full object-contain animate-scale-in"
          />
        )}
      </div>

      {originalImage ? (
        <div className="flex flex-col sm:flex-row justify-center gap-4 animate-fade-in">
          <Button
            variant="destructive"
            onClick={onReset}
            className="w-full sm:w-auto transition-all duration-300 hover:scale-105"
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Reset
          </Button>
          <Button
            onClick={onRemoveBackground}
            disabled={isProcessing}
            className="w-full sm:w-auto bg-gradient-to-r from-purple-600 to-blue-600 transition-all duration-300 hover:scale-105"
          >
            {isProcessing ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin">⚙️</div>
                Processing...
              </div>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Remove Background
              </>
            )}
          </Button>
        </div>
      ) : (
        <div className="space-y-4 animate-fade-in">
          <p className="text-center text-gray-600 font-medium">Try with our sample images:</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {SAMPLE_IMAGES.map((url, index) => (
              <button
                key={index}
                onClick={() => onSampleImageClick(url)}
                className="relative group aspect-square rounded-xl overflow-hidden transition-transform duration-300 hover:scale-105 shadow-md hover:shadow-xl"
              >
                <img
                  src={url}
                  alt={`Sample ${index + 1}`}
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end justify-center pb-4">
                  <p className="text-white text-sm font-medium">Try this image</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
