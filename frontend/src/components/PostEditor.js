import React from 'react';

function PostEditor({ post, setPost, postStatus, setPostStatus, apiClient }) {
  const handlePostToInstagram = async () => {
    try {
      setIsLoading(true);
      setError('');

      // Upload images
      const formData = new FormData();
      selectedImages.forEach((file, index) => {
        formData.append(`image${index}`, file);
      });
      formData.append('post', post);

      // Post to Instagram
      await apiClient.postToInstagram(formData);

      setPostStatus('Post submitted successfully to Instagram!');
    } catch (error) {
      console.error('Error posting to Instagram:', error);
      setError('Failed to post to Instagram. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const shareViaEmail = () => {
    const subject = encodeURIComponent('Check out this real estate post');
    const body = encodeURIComponent(post);
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  };

  const shareViaText = () => {
    const text = encodeURIComponent(post);
    window.location.href = `sms:?body=${text}`;
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(post).then(() => {
      setPostStatus('Post copied to clipboard!');
      setTimeout(() => setPostStatus(''), 3000);
    }, (err) => {
      console.error('Could not copy text: ', err);
      setPostStatus('Failed to copy to clipboard');
    });
  };



  return (
    <div className="post-editor">
      <textarea
        value={post}
        onChange={(e) => setPost(e.target.value)}
        rows="10"
        className="post-textarea"
        data-testid="post-textarea"
      />
      <div className="button-container">
        <button onClick={handlePostToInstagram} className="action-button instagram-button">
          Post to Instagram
        </button>
        <button onClick={shareViaEmail} className="action-button email-button">
          Share via Email
        </button>
        <button onClick={shareViaText} className="action-button text-button">
          Share via Text
        </button>
        <button onClick={copyToClipboard} className="action-button copy-button">
          Copy to Clipboard
        </button>
      </div>
      {postStatus && <p className="post-status">{postStatus}</p>}
    </div>
  );
}

export default PostEditor;
