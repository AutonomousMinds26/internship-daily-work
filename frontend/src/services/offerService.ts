import { api } from './api';
import { OfferItem } from '../types';

export const offerService = {
  getOffers: async (): Promise<OfferItem[]> => {
    const res = await api.get<OfferItem[]>('/offers');
    return res.data;
  },

  getCandidateOffers: async (candidateId: number): Promise<OfferItem[]> => {
    const res = await api.get<OfferItem[]>(`/offers/candidate/${candidateId}`);
    return res.data;
  },

  createOffer: async (offerData: Partial<OfferItem>): Promise<OfferItem> => {
    const res = await api.post<OfferItem>('/offers', offerData);
    return res.data;
  },

  updateOffer: async (id: number, updateData: Partial<OfferItem>): Promise<OfferItem> => {
    const res = await api.put<OfferItem>(`/offers/${id}`, updateData);
    return res.data;
  }
};
