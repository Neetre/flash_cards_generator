import React, { useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Upload, Download, Loader } from 'lucide-react';
import { Flashcard } from '../types';
import toast from 'react-hot-toast';

interface FileUploadProps {
  onFlashcardsReceived: (flashcards: Flashcard[]) => void;
}

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

export function FileUpload({ onFlashcardsReceived }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [language, setLanguage] = useState('english');
  const [numFlashcards, setNumFlashcards] = useState(5);
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [textPreview, setTextPreview] = useState<string>('');
  const { user } = useAuth();

  const validateFile = (selectedFile: File) => {
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError('File size must be less than 5MB');
      return false;
    }
    if (selectedFile.type !== 'application/pdf' && selectedFile.type !== 'text/plain') {
      setError('Please upload a PDF or text file.');
      return false;
    }
    return true;
  };

  const generatePreview = async (selectedFile: File) => {
    if (selectedFile.type === 'text/plain') {
      const text = await selectedFile.text();
      setTextPreview(text.slice(0, 200) + (text.length > 200 ? '...' : ''));
    } else {
      setTextPreview('');
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (validateFile(selectedFile)) {
        setFile(selectedFile);
        setError('');
        await generatePreview(selectedFile);
      }
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('document', file);
    formData.append('language', language);
    formData.append('num_flashcards', numFlashcards.toString());

    try {
      const response = await fetch('http://127.0.0.1:8000/upload', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${user.token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const generatedFlashcards: Flashcard[] = await response.json();
      setFlashcards(generatedFlashcards);
      onFlashcardsReceived(generatedFlashcards);
      toast.success('Flashcards generated successfully!');
    } catch (err) {
      setError('Failed to upload document');
      toast.error('Failed to generate flashcards');
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = () => {
    if (flashcards.length === 0) {
      toast.error('No flashcards to download');
      return;
    }

    const json = JSON.stringify(flashcards, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = 'flashcards.json';
    link.click();

    URL.revokeObjectURL(url);
    toast.success('Flashcards downloaded successfully');
  };

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
        setError('');
        await generatePreview(droppedFile);
      }
    }
  }, []);

  return (
    <div className="max-w-xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <div className="text-center mb-8">
        <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100">
          {uploading ? (
            <Loader className="h-6 w-6 text-blue-600 animate-spin" />
          ) : (
            <Upload className="h-6 w-6 text-blue-600" />
          )}
        </div>
        <h2 className="mt-4 text-2xl font-bold text-gray-900">Upload Document</h2>
        <p className="mt-2 text-sm text-gray-600">Maximum file size: 5MB</p>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      <form onSubmit={handleUpload} className="space-y-4">
        <div
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          className="flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-blue-400 transition-colors duration-200"
        >
          <div className="space-y-1 text-center">
            <input
              type="file"
              onChange={handleFileChange}
              className="sr-only"
              id="file-upload"
              accept=".pdf,.txt"
            />
            <label
              htmlFor="file-upload"
              className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
            >
              <span className="inline-block px-4 py-2">Choose a file</span>
              <span className="block text-sm text-gray-600">or drag and drop here</span>
            </label>
            {file && <p className="text-sm text-gray-600">{file.name}</p>}
          </div>
        </div>

        {textPreview && (
          <div className="mt-4 p-4 bg-gray-50 rounded-md">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Preview:</h3>
            <p className="text-sm text-gray-600 font-mono">{textPreview}</p>
          </div>
        )}

        <div className="flex flex-col space-y-2">
          <label htmlFor="language" className="text-sm font-medium text-gray-700">
            Select Language
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="english">English</option>
            <option value="spanish">Spanish</option>
            <option value="french">French</option>
            <option value="german">German</option>
            <option value="italian">Italian</option>
          </select>
        </div>

        <div className="flex flex-col space-y-2">
          <label htmlFor="num-flashcards" className="text-sm font-medium text-gray-700">
            Number of Flashcards: {numFlashcards}
          </label>
          <input
            type="range"
            id="num-flashcards"
            min="1"
            max="20"
            value={numFlashcards}
            onChange={(e) => setNumFlashcards(Number(e.target.value))}
            className="w-full accent-blue-600"
          />
        </div>

        <button
          type="submit"
          disabled={!file || uploading}
          className="w-full flex justify-center items-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 transition-colors duration-200"
        >
          {uploading ? (
            <>
              <Loader className="animate-spin -ml-1 mr-2 h-4 w-4" />
              Generating...
            </>
          ) : (
            'Generate Flashcards'
          )}
        </button>

        {flashcards.length > 0 && (
          <button
            type="button"
            onClick={handleDownload}
            className="w-full flex justify-center items-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors duration-200"
          >
            <Download className="h-5 w-5 mr-2" />
            Download Flashcards as JSON
          </button>
        )}
      </form>
    </div>
  );
}