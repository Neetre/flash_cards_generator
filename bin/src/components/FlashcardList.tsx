import React, { useState } from 'react';
import { Flashcard } from '../types';
import { ChevronLeft, ChevronRight, RotateCw } from 'lucide-react';

interface FlashcardListProps {
  flashcards: Flashcard[];
}

export function FlashcardList({ flashcards }: FlashcardListProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [mastered, setMastered] = useState<Set<number>>(new Set());

  const currentCard = flashcards[currentIndex];
  const progress = ((currentIndex + 1) / flashcards.length) * 100;

  const handleNext = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev + 1) % flashcards.length);
  };

  const handlePrevious = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev - 1 + flashcards.length) % flashcards.length);
  };

  const toggleMastered = () => {
    setMastered((prev) => {
      const newMastered = new Set(prev);
      if (newMastered.has(currentIndex)) {
        newMastered.delete(currentIndex);
      } else {
        newMastered.add(currentIndex);
      }
      return newMastered;
    });
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Flashcards</h2>
        <div className="mt-2 flex items-center gap-4">
          <div className="flex-1">
            <div className="h-2 bg-gray-200 rounded-full">
              <div
                className="h-2 bg-blue-600 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
          <span className="text-sm text-gray-600">
            {currentIndex + 1} / {flashcards.length}
          </span>
        </div>
      </div>

      <div className="relative perspective-1000">
        <div
          onClick={() => setIsFlipped(!isFlipped)}
          className={`relative w-full aspect-[3/2] cursor-pointer transition-transform duration-500 transform-style-preserve-3d ${
            isFlipped ? 'rotate-y-180' : ''
          }`}
        >
          {/* Front of card */}
          <div className="absolute inset-0 backface-hidden">
            <div className="h-full bg-white rounded-xl shadow-lg p-8 flex flex-col">
              <div className="flex justify-between items-start mb-4">
                <span className="px-3 py-1 text-sm font-semibold rounded-full bg-blue-100 text-blue-800">
                  {currentCard.category}
                </span>
                <span className="px-3 py-1 text-sm font-semibold rounded-full bg-gray-100 text-gray-800">
                  {currentCard.difficulty}
                </span>
              </div>
              <div className="flex-1 flex items-center justify-center">
                <h3 className="text-xl font-semibold text-gray-900 text-center">
                  {currentCard.prompt}
                </h3>
              </div>
              <p className="text-sm text-gray-500 text-center mt-4">Click to flip</p>
            </div>
          </div>

          {/* Back of card */}
          <div className="absolute inset-0 backface-hidden rotate-y-180">
            <div className="h-full bg-white rounded-xl shadow-lg p-8 flex flex-col">
              <div className="flex-1 flex items-center justify-center">
                <p className="text-xl text-gray-800 text-center">{currentCard.answer}</p>
              </div>
              <p className="text-sm text-gray-500 text-center mt-4">Click to flip back</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 flex items-center justify-between">
        <button
          onClick={handlePrevious}
          className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Previous
        </button>

        <button
          onClick={toggleMastered}
          className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            mastered.has(currentIndex)
              ? 'bg-green-100 text-green-800 hover:bg-green-200'
              : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
          }`}
        >
          {mastered.has(currentIndex) ? 'Mastered' : 'Mark as Mastered'}
        </button>

        <button
          onClick={handleNext}
          className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Next
          <ChevronRight className="w-4 h-4 ml-1" />
        </button>
      </div>

      <div className="mt-6">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Mastered: {mastered.size}</span>
          <span>Remaining: {flashcards.length - mastered.size}</span>
        </div>
      </div>
    </div>
  );
}