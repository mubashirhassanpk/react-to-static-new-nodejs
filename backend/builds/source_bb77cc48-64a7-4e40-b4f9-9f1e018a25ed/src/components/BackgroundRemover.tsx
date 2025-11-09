
import React, { useState } from 'react';
import { toast } from './ui/use-toast';
import { removeBackground, loadImage } from '@/utils/backgroundRemoval';
import { Header } from './background-remover/Header';
import { ImageUploadArea } from './background-remover/ImageUploadArea';
import { ProcessedImage } from './background-remover/ProcessedImage';
import { ImageState } from './background-remover/types';

const BackgroundRemover = () => {
  const [imageState, setImageState] = useState<ImageState>({
    originalImage: null,
    processedImage: null,
    isProcessing: false
  });

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast({
        title: "Error",
        description: "Please upload only image files",
        variant: "destructive",
      });
      return;
    }

    try {
      const imageUrl = URL.createObjectURL(file);
      setImageState(prev => ({ ...prev, originalImage: imageUrl, processedImage: null }));
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load image",
        variant: "destructive",
      });
    }
  };

  const handleSampleImageClick = async (url: string) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const imageUrl = URL.createObjectURL(blob);
      setImageState(prev => ({ ...prev, originalImage: imageUrl, processedImage: null }));
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load sample image",
        variant: "destructive",
      });
    }
  };

  const handleRemoveBackground = async () => {
    if (!imageState.originalImage) return;

    setImageState(prev => ({ ...prev, isProcessing: true }));
    try {
      const img = await loadImage(await (await fetch(imageState.originalImage)).blob());
      const processedBlob = await removeBackground(img);
      setImageState(prev => ({
        ...prev,
        processedImage: URL.createObjectURL(processedBlob),
        isProcessing: false
      }));
      toast({
        title: "Success!",
        description: "Background removed successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to remove background",
        variant: "destructive",
      });
      setImageState(prev => ({ ...prev, isProcessing: false }));
    }
  };

  const handleDownload = () => {
    if (!imageState.processedImage) return;
    
    const link = document.createElement('a');
    link.href = imageState.processedImage;
    link.download = 'background-removed.png';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleReset = () => {
    setImageState({
      originalImage: null,
      processedImage: null,
      isProcessing: false
    });
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
      <Header />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <ImageUploadArea
          imageState={imageState}
          onImageUpload={handleImageUpload}
          onSampleImageClick={handleSampleImageClick}
          onReset={handleReset}
          onRemoveBackground={handleRemoveBackground}
        />
        <ProcessedImage
          imageState={imageState}
          onDownload={handleDownload}
        />
      </div>
    </div>
  );
};

export default BackgroundRemover;
