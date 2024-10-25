import React, { useState } from 'react';
import { ArrowUpTrayIcon } from '@heroicons/react/24/outline';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import { API_URL } from '../../utils/api';

interface FileUploadProps {
    onNewMessage: (message: string) => Promise<void>;
}


export default function FileUpload({ onNewMessage }: FileUploadProps) {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [uploadMessage, setUploadMessage] = useState<string | null>(null);
    const [uploadProgress, setUploadProgress] = useState<number>(0);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setFile(event.target.files[0]);
            setUploadMessage(null);
            setUploadProgress(0);
        }
    };

    const handleFileUpload = async () => {
        if (!file) {
            setUploadMessage('Please select a file to upload.');
            return;
        }

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_URL}/api/files/upload/`, true);

        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                const percentComplete = (event.loaded / event.total) * 100;
                console.log(`Upload progress: ${percentComplete}%`);
                setUploadProgress(percentComplete);
            }
        };

        xhr.onload = () => {
            setUploading(false);
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                setUploadMessage(`File uploaded successfully! Extracted text: ${data.extracted_text.substring(0, 100)}...`);
                onNewMessage(`File processed: ${data.extracted_text.substring(0, 100)}...`);
            } else {
                const errorData = JSON.parse(xhr.responseText);
                setUploadMessage(`Failed to upload file: ${errorData.detail || 'Unknown error'}`);
            }
        };

        xhr.onerror = () => {
            setUploading(false);
            setUploadMessage('Error uploading file. Please try again.');
        };

        xhr.send(formData);
    };

    return (
        <div className="file-upload-section">
            <input
                type="file"
                onChange={handleFileChange}
                className="file-input"
                aria-label="Upload a file"
                style={{ display: 'none' }}
                id="file-upload"
            />
            <label htmlFor="file-upload" className="custom-file-upload">
                <ArrowUpTrayIcon className="h-6 w-6" />
                {file ? file.name : 'Choose File'}
            </label>
            <button
                type="button"
                onClick={handleFileUpload}
                className="upload-button"
                disabled={uploading}
            >
                Upload
            </button>
            {uploading && (
                <div style={{ width: 50, height: 50, marginLeft: 10 }}>
                    <CircularProgressbar
                        value={uploadProgress}
                        text={`${Math.round(uploadProgress)}%`}
                        styles={buildStyles({
                            textSize: '16px',
                            pathColor: `rgba(62, 152, 199, ${uploadProgress / 100})`,
                            textColor: '#f88',
                            trailColor: '#d6d6d6',
                        })}
                    />
                </div>
            )}
            {uploadMessage && <p>{uploadMessage}</p>}
        </div>
    );
}
