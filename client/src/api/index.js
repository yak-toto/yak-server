// api/index.js

import axios from 'axios';

const URL = 'http://127.0.0.1:5000';

// ------------------------------
// Auth interface
// ------------------------------

export function postSignup(userData) {
  return axios.post(`${URL}/signup`, userData);
}

export function postLogin(userData) {
  return axios.post(`${URL}/login`, userData);
}

// ------------------------------
// Main interface
// ------------------------------

export function getGroupNames(jwt) {
  return axios.get(`${URL}/groups/names`, { headers: { Authorization: `Bearer: ${jwt}` } });
}

export function getGroup(groupName, jwt) {
  return axios.get(`${URL}/groups/${groupName}`, { headers: { Authorization: `Bearer: ${jwt}` } });
}

export function postMatch(matchId, matchResource, jwt) {
  return axios.post(`${URL}/match/${matchId}`, matchResource, { headers: { Authorization: `Bearer: ${jwt}` } });
}

export function getMatch(team1, team2) {
  return axios.get(`${URL}/match`, { params: { team1, team2 } });
}

export function getScoreBoard(jwt) {
  return axios.get(`${URL}/score_board`, { headers: { Authorization: `Bearer: ${jwt}` } });
}
