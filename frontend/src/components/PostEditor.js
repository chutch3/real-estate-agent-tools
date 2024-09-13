import React from 'react';
import { TextField } from '@mui/material';

function PostEditor({ post, setPost, postStatus, setPostStatus, setIsLoading, setError, selectedImages }) {

  return (
    <div className="post-editor">
      <TextField
        multiline
        rows={6}
        value={post}
        onChange={(e) => setPost(e.target.value)}
        fullWidth
        variant="outlined"
        margin="normal"
      />
      {postStatus && <p className="post-status">{postStatus}</p>}
    </div>
  );
}

export default PostEditor;
