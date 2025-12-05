/**
 * CombatAnimations.js
 * Handles combat visual effects and animations
 * 
 * Features:
 * - Damage/healing number animations
 * - Status effect animations
 * - Attack/skill visual effects
 * - Screen shake
 */

class CombatAnimations {
    constructor() {
        this.animationSpeed = 1; // 1 = normal, 2 = fast, 0.5 = slow
        this.effectsContainer = document.getElementById('damage-numbers-container') || document.body;
        
        console.log('[CombatAnimations] Initialized');
    }
    
    // ========================================================================
    // DAMAGE NUMBERS
    // ========================================================================
    
    /**
     * Show damage number animation
     * 
     * @param {string} targetId - Participant ID
     * @param {number} damage - Damage amount
     * @param {boolean} isCritical - Is this a critical hit?
     */
    async showDamage(targetId, damage, isCritical = false) {
        console.log('[CombatAnimations] Showing damage:', targetId, damage, isCritical);
        
        const target = this.getElementByParticipantId(targetId);
        if (!target) {
            console.warn('[CombatAnimations] Target element not found:', targetId);
            return;
        }
        
        // Create damage number
        const damageNumber = document.createElement('div');
        damageNumber.className = `damage-number ${isCritical ? 'critical' : ''}`;
        damageNumber.textContent = `-${damage}`;
        
        // Position at center of target
        this.positionAtElement(damageNumber, target);
        
        // Add to container
        this.effectsContainer.appendChild(damageNumber);
        
        // Animate
        const duration = 1000 / this.animationSpeed;
        await this.delay(duration);
        
        // Remove
        damageNumber.remove();
        
        // Shake target card
        this.shakeElement(target);
    }
    
    /**
     * Show healing number animation
     */
    async showHealing(targetId, healing) {
        console.log('[CombatAnimations] Showing healing:', targetId, healing);
        
        const target = this.getElementByParticipantId(targetId);
        if (!target) {
            console.warn('[CombatAnimations] Target element not found:', targetId);
            return;
        }
        
        // Create healing number
        const healingNumber = document.createElement('div');
        healingNumber.className = 'healing-number';
        healingNumber.textContent = `+${healing}`;
        
        // Position at center of target
        this.positionAtElement(healingNumber, target);
        
        // Add to container
        this.effectsContainer.appendChild(healingNumber);
        
        // Animate
        const duration = 1000 / this.animationSpeed;
        await this.delay(duration);
        
        // Remove
        healingNumber.remove();
    }
    
    /**
     * Show miss text
     */
    async showMiss(targetId) {
        console.log('[CombatAnimations] Showing miss:', targetId);
        
        const target = this.getElementByParticipantId(targetId);
        if (!target) return;
        
        // Create miss text
        const missText = document.createElement('div');
        missText.className = 'miss-text';
        missText.textContent = 'MISS!';
        
        // Position at center of target
        this.positionAtElement(missText, target);
        
        // Add to container
        this.effectsContainer.appendChild(missText);
        
        // Animate
        const duration = 1000 / this.animationSpeed;
        await this.delay(duration);
        
        // Remove
        missText.remove();
    }
    
    // ========================================================================
    // EFFECT ANIMATIONS
    // ========================================================================
    
    /**
     * Show status effect application
     */
    async showEffect(targetId, effectType) {
        console.log('[CombatAnimations] Showing effect:', targetId, effectType);
        
        const target = this.getElementByParticipantId(targetId);
        if (!target) return;
        
        const effectIcons = {
            'rage': '🔥',
            'inspiration': '🎵',
            'heal': '✨',
            'buff': '⬆️',
            'debuff': '⬇️',
            'wild_shape': '🐾',
            'channel_divinity': '⚡',
            'defend': '🛡️'
        };
        
        const icon = effectIcons[effectType] || '✨';
        
        // Create effect element
        const effectElement = document.createElement('div');
        effectElement.className = `effect-animation ${effectType}`;
        effectElement.textContent = icon;
        
        // Position at center of target
        this.positionAtElement(effectElement, target);
        
        // Add to container
        this.effectsContainer.appendChild(effectElement);
        
        // Animate
        const duration = 1500 / this.animationSpeed;
        await this.delay(duration);
        
        // Remove
        effectElement.remove();
    }
    
    /**
     * Flash effect for buff/debuff
     */
    flashElement(element, color = 'rgba(255, 215, 0, 0.3)') {
        const originalBg = element.style.backgroundColor;
        
        element.style.transition = 'background-color 0.2s';
        element.style.backgroundColor = color;
        
        setTimeout(() => {
            element.style.backgroundColor = originalBg;
        }, 200);
    }
    
    // ========================================================================
    // SCREEN EFFECTS
    // ========================================================================
    
    /**
     * Shake an element
     */
    shakeElement(element) {
        if (!element) return;
        
        element.classList.add('shake');
        setTimeout(() => {
            element.classList.remove('shake');
        }, 500 / this.animationSpeed);
    }
    
    /**
     * Screen shake effect
     */
    shakeScreen(intensity = 1) {
        const body = document.body;
        const shakeAmount = 10 * intensity;
        
        let shakeCount = 0;
        const maxShakes = 5;
        
        const shakeInterval = setInterval(() => {
            if (shakeCount >= maxShakes) {
                clearInterval(shakeInterval);
                body.style.transform = '';
                return;
            }
            
            const x = (Math.random() - 0.5) * shakeAmount;
            const y = (Math.random() - 0.5) * shakeAmount;
            
            body.style.transform = `translate(${x}px, ${y}px)`;
            shakeCount++;
        }, 50 / this.animationSpeed);
    }
    
    // ========================================================================
    // ATTACK ANIMATIONS
    // ========================================================================
    
    /**
     * Animate an attack from attacker to target
     */
    async animateAttack(attackerId, targetId) {
        console.log('[CombatAnimations] Animating attack:', attackerId, '->', targetId);
        
        const attacker = this.getElementByParticipantId(attackerId);
        const target = this.getElementByParticipantId(targetId);
        
        if (!attacker || !target) return;
        
        // Create projectile or slash effect
        const projectile = document.createElement('div');
        projectile.className = 'attack-projectile';
        projectile.textContent = '⚔️';
        
        // Start position (attacker)
        const attackerRect = attacker.getBoundingClientRect();
        const targetRect = target.getBoundingClientRect();
        
        projectile.style.position = 'fixed';
        projectile.style.left = `${attackerRect.left + attackerRect.width / 2}px`;
        projectile.style.top = `${attackerRect.top + attackerRect.height / 2}px`;
        projectile.style.fontSize = '2rem';
        projectile.style.zIndex = '9999';
        
        document.body.appendChild(projectile);
        
        // Animate to target
        const duration = 300 / this.animationSpeed;
        projectile.style.transition = `all ${duration}ms ease-out`;
        
        // Trigger animation
        requestAnimationFrame(() => {
            projectile.style.left = `${targetRect.left + targetRect.width / 2}px`;
            projectile.style.top = `${targetRect.top + targetRect.height / 2}px`;
            projectile.style.transform = 'scale(1.5)';
            projectile.style.opacity = '0';
        });
        
        // Wait for animation
        await this.delay(duration);
        
        // Remove projectile
        projectile.remove();
    }
    
    // ========================================================================
    // SPELL EFFECTS
    // ========================================================================
    
    /**
     * Show spell cast effect
     */
    async showSpellCast(casterId, targetId = null, spellType = 'generic') {
        console.log('[CombatAnimations] Showing spell cast:', casterId, spellType);
        
        const caster = this.getElementByParticipantId(casterId);
        if (!caster) return;
        
        // Show casting effect on caster
        const castEffect = document.createElement('div');
        castEffect.className = `spell-cast-effect ${spellType}`;
        castEffect.innerHTML = '✨';
        
        this.positionAtElement(castEffect, caster);
        this.effectsContainer.appendChild(castEffect);
        
        await this.delay(500 / this.animationSpeed);
        castEffect.remove();
        
        // If there's a target, show spell projectile
        if (targetId) {
            await this.animateSpellProjectile(casterId, targetId, spellType);
        }
    }
    
    /**
     * Animate spell projectile
     */
    async animateSpellProjectile(casterId, targetId, spellType) {
        const caster = this.getElementByParticipantId(casterId);
        const target = this.getElementByParticipantId(targetId);
        
        if (!caster || !target) return;
        
        const spellIcons = {
            'fire': '🔥',
            'ice': '❄️',
            'lightning': '⚡',
            'heal': '✨',
            'buff': '⭐',
            'generic': '✨'
        };
        
        const icon = spellIcons[spellType] || spellIcons['generic'];
        
        // Create projectile
        const projectile = document.createElement('div');
        projectile.className = 'spell-projectile';
        projectile.textContent = icon;
        
        // Position and animate
        const casterRect = caster.getBoundingClientRect();
        const targetRect = target.getBoundingClientRect();
        
        projectile.style.position = 'fixed';
        projectile.style.left = `${casterRect.left + casterRect.width / 2}px`;
        projectile.style.top = `${casterRect.top + casterRect.height / 2}px`;
        projectile.style.fontSize = '2.5rem';
        projectile.style.zIndex = '9999';
        
        document.body.appendChild(projectile);
        
        const duration = 400 / this.animationSpeed;
        projectile.style.transition = `all ${duration}ms ease-in-out`;
        
        requestAnimationFrame(() => {
            projectile.style.left = `${targetRect.left + targetRect.width / 2}px`;
            projectile.style.top = `${targetRect.top + targetRect.height / 2}px`;
        });
        
        await this.delay(duration);
        projectile.remove();
    }
    
    // ========================================================================
    // UTILITIES
    // ========================================================================
    
    /**
     * Get element by participant ID
     */
    getElementByParticipantId(participantId) {
        return document.querySelector(`[data-participant-id="${participantId}"]`);
    }
    
    /**
     * Position element at center of another element
     */
    positionAtElement(element, targetElement) {
        const rect = targetElement.getBoundingClientRect();
        
        element.style.position = 'fixed';
        element.style.left = `${rect.left + rect.width / 2}px`;
        element.style.top = `${rect.top + rect.height / 2}px`;
        element.style.transform = 'translate(-50%, -50%)';
        element.style.zIndex = '9999';
        element.style.pointerEvents = 'none';
    }
    
    /**
     * Delay helper
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Set animation speed
     */
    setSpeed(speed) {
        this.animationSpeed = Math.max(0.1, Math.min(5, speed));
        console.log('[CombatAnimations] Speed set to:', this.animationSpeed);
    }
}

// Export for global use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CombatAnimations;
}