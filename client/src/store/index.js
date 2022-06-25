import Vue from 'vue'
import Vuex from 'vuex'

import { postSignup, postLogin, getGroupNames, getGroup, postMatch, getMatch, getScoreBoard, postLogout } from '@/api'
import { isValidJwt, EventBus } from '@/utils'

const state = {
  matches: [],
  currentMatches: [],
  user: {},
  jwt: ''
}

const actions = {
  getGroup(context, { group_name }) {
    return getGroup(group_name, context.state.jwt.token)
  },
  postMatch(context, { match_id, match_resource }) {
    console.log(context.state.jwt.token)
    return postMatch(match_id, match_resource, context.state.jwt.token)
  },
  getScoreBoard(context) {
    return getScoreBoard(context.state.jwt.token)
  },
  getGroupNames(context) {
    return getGroupNames(context.state.jwt.token)
  },
  // asynchronous operations
  login(context, userData) {
    context.commit('setUserData', { userData })
    return postLogin(userData)
      .then(response => context.commit('setJwtToken', { jwt: response.data }))
      .catch(error => {
        console.log('Error Authenticating: ', error)
        // EventBus.emit('failedAuthentication', error)
      })
  },
  signup(context, userData) {
    context.commit('setUserData', { userData })
    return postSignup(userData)
      .then(response => context.dispatch('login', userData))
      .catch(error => {
        console.log('Error Registering: ', error)
        // EventBus.emit('failedRegistering: ', error)
      })
  },
  logout(context) {
    context.commit('eraseJwtToken')
  },
}

const mutations = {
  setUserData(state, payload) {
    console.log('setUserData payload = ', payload)
    state.userData = payload.userData
  },
  setJwtToken(state, payload) {
    console.log('setJwtToken payload = ', payload)
    localStorage.token = payload.jwt.token
    state.jwt = payload.jwt
  },
  eraseJwtToken(state) {
    console.log('delete token')
    localStorage.token = "deleted"
    state.jwt = "deleted"
  }
}

const getters = {
  // reusable data accessors
  isAuthenticated (state) {
    return isValidJwt(state.jwt.token)
  }
}

const store = new Vuex.Store({
  state,
  actions,
  mutations,
  getters
})

export default store
