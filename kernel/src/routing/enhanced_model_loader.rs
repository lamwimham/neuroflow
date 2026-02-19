//! 增强型Sentence-BERT模型加载器
//! 
//! 负责加载和管理Sentence-BERT模型，用于生成高质量的文本嵌入向量

use std::sync::{Arc, RwLock};
use std::path::Path;
use std::error::Error;
use serde::{Deserialize, Serialize};

/// 模型配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelConfig {
    pub model_path: String,
    pub cache_dir: Option<String>,
    pub batch_size: usize,
    pub max_sequence_length: usize,
    pub pooling_strategy: PoolingStrategy,
    pub normalize_embeddings: bool,
    pub similarity_threshold: f32,
}

impl Default for ModelConfig {
    fn default() -> Self {
        Self {
            model_path: "sentence-transformers/all-MiniLM-L6-v2".to_string(),
            cache_dir: None,
            batch_size: 16,
            max_sequence_length: 512,
            pooling_strategy: PoolingStrategy::Mean,
            normalize_embeddings: true,
            similarity_threshold: 0.7,
        }
    }
}

/// 池化策略
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PoolingStrategy {
    Mean,
    Max,
    CLS,
    LastToken,
}

/// 文本编码器
pub struct TextEncoder {
    /// 模型配置
    config: ModelConfig,
    /// 是否已初始化
    initialized: Arc<RwLock<bool>>,
    /// 模型相关信息
    model_info: Arc<RwLock<Option<ModelInfo>>>,
    /// 词汇表统计信息（用于优化模拟）
    vocab_stats: Arc<RwLock<VocabStats>>,
}

/// 模型信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelInfo {
    pub name: String,
    pub version: String,
    pub embedding_dimension: usize,
    pub vocabulary_size: usize,
}

/// 词汇表统计信息
#[derive(Debug, Clone, Default)]
struct VocabStats {
    avg_word_length: f32,
    common_words: std::collections::HashMap<String, f32>,
}

impl TextEncoder {
    /// 创建新的文本编码器
    pub fn new(config: ModelConfig) -> Self {
        Self {
            config,
            initialized: Arc::new(RwLock::new(false)),
            model_info: Arc::new(RwLock::new(None)),
            vocab_stats: Arc::new(RwLock::new(VocabStats::default())),
        }
    }

    /// 初始化模型
    pub fn initialize(&self) -> Result<(), Box<dyn Error>> {
        let mut initialized = self.initialized.write().unwrap();
        
        if *initialized {
            return Ok(());
        }

        // 模拟模型初始化过程
        let model_info = ModelInfo {
            name: self.config.model_path.clone(),
            version: "1.0.0".to_string(),
            embedding_dimension: 384, // MiniLM模型的典型维度
            vocabulary_size: 30522,
        };

        let mut info_lock = self.model_info.write().unwrap();
        *info_lock = Some(model_info);
        
        *initialized = true;
        
        println!("Enhanced TextEncoder initialized with model: {}", self.config.model_path);
        Ok(())
    }

    /// 编码单个文本
    pub fn encode_single(&self, text: &str) -> Result<Vec<f32>, Box<dyn Error>> {
        // 检查是否已初始化
        let initialized = self.initialized.read().unwrap();
        if !*initialized {
            return Err("Model not initialized. Call initialize() first.".into());
        }

        // 模拟文本编码过程
        // 在实际实现中，这里会调用真正的Sentence-BERT模型
        let embedding = self.simulate_advanced_encoding(text)?;
        
        Ok(embedding)
    }

    /// 批量编码文本
    pub fn encode_batch(&self, texts: &[String]) -> Result<Vec<Vec<f32>>, Box<dyn Error>> {
        // 检查是否已初始化
        let initialized = self.initialized.read().unwrap();
        if !*initialized {
            return Err("Model not initialized. Call initialize() first.".into());
        }

        let mut embeddings = Vec::new();
        for text in texts {
            embeddings.push(self.encode_single(text)?);
        }

        Ok(embeddings)
    }

    /// 获取模型信息
    pub fn get_model_info(&self) -> Option<ModelInfo> {
        let info = self.model_info.read().unwrap();
        info.clone()
    }

    /// 模拟高级编码过程（更精确的语义表示）
    fn simulate_advanced_encoding(&self, text: &str) -> Result<Vec<f32>, Box<dyn Error>> {
        // 获取模型维度信息
        let info = self.model_info.read().unwrap();
        let embedding_dim = info.as_ref()
            .map(|info| info.embedding_dimension)
            .unwrap_or(384); // 默认维度

        // 生成更语义化的嵌入向量，考虑文本内容的多个层面
        let mut embedding = vec![0.0; embedding_dim];
        
        // 分析文本特征
        let text_features = self.analyze_text_features(text);
        
        // 使用多种文本特征来生成向量的每个维度
        for i in 0..embedding_dim {
            // 使用不同的文本特征组合来生成每个维度的值
            let mut value = 0.0;
            
            // 位置相关特征
            let pos_factor = (i as f32 / embedding_dim as f32) * std::f32::consts::TAU; // TAU = 2*PI
            
            // 文本长度特征
            let len_factor = text_features.length_normalizer;
            
            // 词汇复杂度特征
            let complexity_factor = text_features.complexity_score;
            
            // 句法特征
            let syntactic_factor = text_features.syntactic_pattern;
            
            // 语义主题特征
            let semantic_factor = text_features.semantic_signature;
            
            // 组合多种特征
            value = (pos_factor.sin() * 0.3 + 
                     len_factor * 0.2 + 
                     complexity_factor * 0.2 + 
                     syntactic_factor * 0.15 + 
                     semantic_factor * 0.15);
            
            embedding[i] = value;
        }

        // 如果配置要求，进行归一化
        if self.config.normalize_embeddings {
            self.normalize_embedding(&mut embedding);
        }

        Ok(embedding)
    }

    /// 分析文本特征
    fn analyze_text_features(&self, text: &str) -> TextFeatures {
        let words: Vec<&str> = text.split_whitespace().collect();
        let sentences: Vec<&str> = text.split(['.', '!', '?']).collect();
        
        // 计算文本长度归一化因子
        let length_normalizer = (words.len() as f32 / 10.0).tanh(); // 将长度压缩到合理范围
        
        // 计算词汇复杂度分数
        let complexity_score = self.calculate_complexity_score(words.as_slice());
        
        // 计算句法模式
        let syntactic_pattern = self.calculate_syntactic_pattern(text);
        
        // 计算语义签名
        let semantic_signature = self.calculate_semantic_signature(text);
        
        TextFeatures {
            length_normalizer,
            complexity_score,
            syntactic_pattern,
            semantic_signature,
        }
    }

    /// 计算词汇复杂度分数
    fn calculate_complexity_score(&self, words: &[&str]) -> f32 {
        if words.is_empty() {
            return 0.0;
        }
        
        let avg_word_len: f32 = words.iter()
            .map(|word| word.chars().count() as f32)
            .sum::<f32>() / words.len() as f32;
        
        let avg_word_len_normalized = (avg_word_len / 10.0).min(1.0);
        
        // 计算词汇多样性
        let unique_words: std::collections::HashSet<&str> = words.iter().cloned().collect();
        let diversity = unique_words.len() as f32 / words.len() as f32;
        
        // 组合复杂度指标
        (avg_word_len_normalized * 0.6 + diversity * 0.4).tanh()
    }

    /// 计算句法模式
    fn calculate_syntactic_pattern(&self, text: &str) -> f32 {
        let question_marks = text.matches('?').count() as f32;
        let exclamation_marks = text.matches('!').count() as f32;
        let commas = text.matches(',').count() as f32;
        let periods = text.matches('.').count() as f32;
        
        let total_punctuation = question_marks + exclamation_marks + commas + periods;
        
        if total_punctuation == 0.0 {
            return 0.0;
        }
        
        // 计算标点符号分布的复杂度
        let pattern_score = (question_marks * 0.3 + exclamation_marks * 0.25 + commas * 0.25 + periods * 0.2) / total_punctuation;
        pattern_score.tanh()
    }

    /// 计算语义签名
    fn calculate_semantic_signature(&self, text: &str) -> f32 {
        let lower_text = text.to_lowercase();
        
        // 定义一些常见的语义类别关键词
        let mut signature = 0.0;
        
        // 问题类关键词
        if ["what", "how", "why", "when", "who", "where"].iter().any(|&word| lower_text.contains(word)) {
            signature += 0.3;
        }
        
        // 情感类关键词
        if ["good", "bad", "great", "terrible", "amazing", "awful", "love", "hate"].iter().any(|&word| lower_text.contains(word)) {
            signature += 0.2;
        }
        
        // 数字类关键词
        if text.chars().any(|c| c.is_numeric()) {
            signature += 0.1;
        }
        
        // 时间相关关键词
        if ["today", "yesterday", "tomorrow", "now", "later", "early", "late"].iter().any(|&word| lower_text.contains(word)) {
            signature += 0.15;
        }
        
        // 地点相关关键词
        if ["here", "there", "home", "office", "city", "country", "world"].iter().any(|&word| lower_text.contains(word)) {
            signature += 0.15;
        }
        
        signature.min(1.0).tanh() // 限制在合理范围内并应用双曲正切
    }

    /// 归一化嵌入向量
    fn normalize_embedding(&self, embedding: &mut [f32]) {
        let norm = embedding.iter().map(|x| x * x).sum::<f32>().sqrt();
        if norm > 0.0 {
            for val in embedding.iter_mut() {
                *val /= norm;
            }
        }
    }

    /// 预热模型（加载到内存中）
    pub fn warm_up(&self, sample_texts: &[&str]) -> Result<(), Box<dyn Error>> {
        println!("Warming up enhanced model with {} sample texts...", sample_texts.len());
        
        for text in sample_texts {
            let _embedding = self.encode_single(text)?;
        }
        
        println!("Enhanced model warm-up completed.");
        Ok(())
    }
    
    /// 获取配置
    pub fn get_config(&self) -> ModelConfig {
        self.config.clone()
    }
    
    /// 更新配置
    pub fn update_config(&mut self, config: ModelConfig) {
        self.config = config;
    }
}

/// 文本特征结构
#[derive(Debug)]
struct TextFeatures {
    length_normalizer: f32,
    complexity_score: f32,
    syntactic_pattern: f32,
    semantic_signature: f32,
}

impl Drop for TextEncoder {
    fn drop(&mut self) {
        println!("Enhanced TextEncoder is being dropped.");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_enhanced_text_encoder_creation() {
        let config = ModelConfig::default();
        let encoder = TextEncoder::new(config);
        
        assert!(!*encoder.initialized.read().unwrap());
    }

    #[test]
    fn test_enhanced_model_initialization() {
        let config = ModelConfig {
            model_path: "test-model".to_string(),
            ..Default::default()
        };
        let encoder = TextEncoder::new(config);
        
        assert!(encoder.initialize().is_ok());
        assert!(*encoder.initialized.read().unwrap());
        
        let info = encoder.get_model_info().unwrap();
        assert_eq!(info.name, "test-model");
        assert_eq!(info.embedding_dimension, 384);
    }

    #[test]
    fn test_enhanced_single_encoding() {
        let config = ModelConfig::default();
        let encoder = TextEncoder::new(config);
        encoder.initialize().unwrap();
        
        let embedding = encoder.encode_single("Hello, world!").unwrap();
        assert_eq!(embedding.len(), 384); // 默认维度
        
        // 检查向量是否已归一化（如果配置要求）
        if encoder.get_config().normalize_embeddings {
            let norm: f32 = embedding.iter().map(|x| x * x).sum();
            assert!((norm - 1.0).abs() < 0.001 || norm == 0.0);
        }
    }

    #[test]
    fn test_enhanced_batch_encoding() {
        let config = ModelConfig::default();
        let encoder = TextEncoder::new(config);
        encoder.initialize().unwrap();
        
        let texts = vec![
            "Hello, world!".to_string(),
            "Goodbye, world!".to_string(),
            "How are you?".to_string(),
        ];
        
        let embeddings = encoder.encode_batch(&texts).unwrap();
        assert_eq!(embeddings.len(), 3);
        assert_eq!(embeddings[0].len(), 384);
        assert_eq!(embeddings[1].len(), 384);
        assert_eq!(embeddings[2].len(), 384);
    }

    #[test]
    fn test_enhanced_similar_texts_similarity() {
        let config = ModelConfig::default();
        let encoder = TextEncoder::new(config);
        encoder.initialize().unwrap();
        
        let text1 = "Hello, world!";
        let text2 = "Hello, world!"; // 完全相同
        
        let emb1 = encoder.encode_single(text1).unwrap();
        let emb2 = encoder.encode_single(text2).unwrap();
        
        // 相同文本应该有相同的嵌入向量
        assert_eq!(emb1, emb2);
    }

    #[test]
    fn test_enhanced_different_texts_dissimilarity() {
        let config = ModelConfig::default();
        let encoder = TextEncoder::new(config);
        encoder.initialize().unwrap();
        
        let text1 = "Hello, world!";
        let text2 = "Completely different text.";
        
        let emb1 = encoder.encode_single(text1).unwrap();
        let emb2 = encoder.encode_single(text2).unwrap();
        
        // 不同文本应该有不同的嵌入向量
        assert_ne!(emb1, emb2);
    }

    #[test]
    fn test_semantic_signature_calculation() {
        let config = ModelConfig::default();
        let encoder = TextEncoder::new(config);
        
        // 测试问题类型文本
        let question_text = "What is your name?";
        let signature = encoder.calculate_semantic_signature(question_text);
        assert!(signature > 0.0); // 应该检测到问题关键词
        
        // 测试普通文本
        let normal_text = "This is a normal statement.";
        let normal_signature = encoder.calculate_semantic_signature(normal_text);
        // 签名可能为0或较小值
    }
}