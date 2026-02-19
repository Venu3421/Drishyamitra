from deepface import DeepFace
import os
import shutil
from fastapi import UploadFile
import numpy as np
import cv2

# Ensure models are downloaded or handled
# DeepFace automatically downloads models to ~/.deepface/weights/

class FaceRecognitionService:
    @staticmethod
    def generate_embedding(img_path: str):
        try:
            # multiple faces? enforce_detection=False to avoid error if no face
            embedding_objs = DeepFace.represent(
                img_path=img_path,
                model_name="Facenet512",
                enforce_detection=False
            )
            # Return first detection for now, or all
            if embedding_objs:
                return [obj["embedding"] for obj in embedding_objs]
            return []
        except Exception as e:
            print(f"Error in generating embedding: {e}")
            return []

    @staticmethod
    def find_matches(img_path: str, db_path: str):
        # db_path should be a folder with images to compare against
        try:
            dfs = DeepFace.find(
                img_path=img_path,
                db_path=db_path,
                model_name="Facenet512",
                enforce_detection=False
            )
            return dfs
        except Exception as e:
            print(f"Error in finding matches: {e}")
            return []
